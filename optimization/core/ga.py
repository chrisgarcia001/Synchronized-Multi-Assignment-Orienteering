#-----------------------------------------------------------------------------------------------------
# Author: cgarcia@umw.edu
# Created: 9/11/2020
# About: This file contains the main genetic algorithm implementations and requisite structures 
#        for solving the Synchronized Multi-Assignment Orienteering problem.
#
# Revision History:
# Date        Author            Change Description
# 9/1/2020    cgarcia           Initial version.
#-----------------------------------------------------------------------------------------------------

import os
import time
import json
import random as rnd
import util_data as du
from structs import *
from functools import *
import joblib as jb

# ========== Genetic Algorithm-Related Code ==========================================================
        
# This class represents a mutable solution representation for GA for this problem.
class GAEncodedSolution:
    def __init__(self, problem, job_nodes=None):
        self.job_nodes = []
        if job_nodes == None:
            self.job_nodes = [build_node_object(problem, i) for i in job_node_inds(problem)]
        else:
            self.job_nodes = [j.clone() for j in job_nodes]
        self.job_node_dict = dict([(j.node_id, j) for j in self.job_nodes])
        self.problem = problem
        
    def clone(self):
        return GAEncodedSolution(self.problem, self.job_nodes)

# ---------- Solution construction utility functions -------------------------------------------------

# Constructs an assignment set object by sequentially adding the job nodes of the encoded solution
# in their given order. This will contain a functional solution.
# @param encoded_solution: an EncodedSolution object
# @returns: an AssignmentSet consisting the solution.
def construct_assignment_set(encoded_solution):
    asmts = AssignmentSet(encoded_solution.problem)
    tabu = set()
    for j in encoded_solution.job_nodes:
        if not(j.node_id in tabu) and asmts.insert_node(j):
            tabu = tabu.union(j.conflict_ids)
    return asmts

# ---------- Population initializers, fitness functions, mutators, and crossover operators ---------

# Constructs a mutator function f : {encoded_solution} -> {encoded_solution}
# @param max_swap_dist: the maximum number of ordered job nodes apart that can be swapped
# @param n_swap_probs: a list of probabilities addint to 1. Each position contains the probability 
#                      of having that many swaps. (e.g. index 0 has the probability of having no swaps).
# @param max_start_time_change_frac: the max fraction of the time window that the start time can change.
# @param start_time_change_prob: the probability that an individual job has its start time changed.
# @returns: the mutator function
def build_mutator_f(max_swap_dist, n_swap_probs, max_start_time_change_frac, start_time_change_prob):
    def mutate(encoded_sol):
        encoded_sol = encoded_sol.clone()
        n_swap = du.random_weighted_index(n_swap_probs)
        for i in range(n_swap):
            j = rnd.randint(0, len(encoded_sol.job_nodes) - 1)
            k = j + rnd.randint(1, max_swap_dist)
            k = k if k < len(encoded_sol.job_nodes) else j - rnd.randint(1, max_swap_dist)
            t = encoded_sol.job_nodes[j]
            encoded_sol.job_nodes[j] = encoded_sol.job_nodes[k]
            encoded_sol.job_nodes[k] = t
        for j in encoded_sol.job_nodes:
            if rnd.random() <= start_time_change_prob:
                c = du.rand_float(0, j.time_window_length()) 
                nt = j.start_time + c if rnd.random() > 0.5 else j.start_time + c
                nt = max(min(nt, j.closew), j.openw)
                j.start_time = nt
        return encoded_sol
    return mutate

# Builds a crossover function of form f : {encoded_solution} X {encoded_solution} -> {encoded_solution}
# More detail: Makes a copy of first solution and them randomly sets a random set of 
#              job node start times to those of the second.
# @param min_job_frac: the minimum fraction of job nodes from s2 to swap into s1
# @param max_job_frac: the maximum fraction of job nodes from s2 to swap into s1
# @returns: the crossover function
def build_crossover_f(min_job_frac, max_job_frac):
    def crossover(es1, es2):
        new_es = es1.clone()
        a, b = [int(round(f * len(new_es.job_nodes))) for f in [min_job_frac, max_job_frac]]
        swap_inds = rnd.sample([j.node_id for j in new_es.job_nodes], rnd.randint(a, b))
        for i in swap_inds:
            new_es.job_node_dict[i].start_time = es2.job_node_dict[i].start_time 
        return new_es
    return crossover

# This is a fitness function based on the total reward. 
# @param encoded_sol: an encoded solution
# @returns: a number representing the objective function of the encoded solution.
def objective_f(encoded_sol):
    return construct_assignment_set(encoded_sol).reward

# This is a fitness function based on the square of the objective function. 
# Higher-reward solutions will have an even greater probability of being selected. 
# @param encoded_sol: an encoded solution
# @returns: a number representing the objective function of the encoded solution.
def objective_f_squared(encoded_sol):
    return objective_f(encoded_sol) ** 2

# Randomize the start times within each job node's time window.
def randomize_start_times(job_nodes):
    for j in job_nodes:
        j.start_time = du.rand_float(j.openw, j.closew)
 
# Constructs a fully-randomized initial population: randomized job node ordering and start times. 
# @param problem: a BaseProblem object
# @param n: the population size
# @returns: a list of GAEncodedSolution objects of length n.
def randomized_initial_population(problem, n):
    pop = []
    for i in range(n):
        es = GAEncodedSolution(problem)
        randomize_start_times(es.job_nodes)
        rnd.shuffle(es.job_nodes)
        pop.append(es)
    return pop    

# Constructs an initial population in best-reward-first order with random start times.
# @param problem: a BaseProblem object
# @param n: the population size
# @returns: a list of GAEncodedSolution objects of length n.
def best_reward_first_initial_population(problem, n):
    pop = []
    for i in range(n):
        es = GAEncodedSolution(problem)
        randomize_start_times(es.job_nodes)
        es.job_nodes = sorted(es.job_nodes, key=lambda x: -x.reward)
        pop.append(es)
    return pop  

# Constructs a function from multiple population initializers containing the specified
# fraction of the initial population generated by each initializer. 
# @param generators: a list of form [(f(problem, n), fraction)]
# @returns: a function of form f : {problem} X {integer} -> {[GAEncodedSolution]}
def initial_population_gen_pipeline(generators):
    def pipeline(problem, n):
        pop = []
        for (f, frac) in generators:
            pop += f(problem, int(frac * n))
        return pop
    return pipeline

# ---------- Genetic Algorithm Core ---------------------------------------------------------------- 
class GeneticAlgorithm:
    def __init__(self, initial_pop, mutator_f, crossover_f, fitness_f, max_iterations,
                 max_unimprove_time, elitism_proportion, n_parallel_jobs=1, verbose=True):
        self.initial_population = initial_pop
        self.mutator_f = mutator_f
        self.crossover_f = crossover_f
        self.fitness_f = fitness_f
        self.max_iterations = max_iterations
        self.max_unimprove_time = max_unimprove_time
        self.elitism_proportion = elitism_proportion
        self.n_parallel_jobs = n_parallel_jobs
        self.verbose = verbose
    
    def solve(self):
        nj = self.n_parallel_jobs 
        i = 1
        last_improve_time = time.time()
        start_time = time.time()
        pop = self.initial_population
        fits = jb.Parallel(n_jobs=nj)(jb.delayed(self.fitness_f)(e) for e in pop)
        ev = sorted(list(zip(pop, fits)), key=lambda x:x[1])
        best = ev[len(ev) - 1]
        rw = lambda wts: du.random_weighted_index(wts)
        sol_maker = lambda fts, evs: lambda x: self.mutator_f(self.crossover_f(evs[rw(fts)][0], evs[rw(fts)][0]))
        while i <= self.max_iterations and time.time() <= last_improve_time + self.max_unimprove_time:
            elite = ev[int((1 - self.elitism_proportion) * len(self.initial_population)):]
            pop = []
            f = sol_maker(fits, ev)
            n = len(self.initial_population) - len(elite)
            pop = jb.Parallel(n_jobs=nj)(jb.delayed(f)(i) for i in range(n))
            fits = jb.Parallel(n_jobs=nj)(jb.delayed(self.fitness_f)(e) for e in pop)
            ev = sorted(list(zip(pop, fits)) + elite, key=lambda x:x[1])
            if ev[len(ev) - 1][1] > best[1]:
                best = ev[len(ev) - 1]
                last_improve_time = time.time()
            etime = time.time() - start_time
            if self.verbose:
                print('Iteration ' + str(i) + ': Best Fitness=' + str(best[1]) + ', Elapsed Time: ' + str(etime))
            i += 1
        return {'solution': best[0], 'elapsed_time': etime}
            
    
    
        
