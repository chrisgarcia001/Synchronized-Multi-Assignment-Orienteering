#-----------------------------------------------------------------------------------------------------
# Author: cgarcia@umw.edu
# Created: 9/12/2020
# About: This file contains the main ALNS implementations and requisite structures for solving 
#        the Synchronized Multi-Assignment Orienteering problem. The main algorithm is problem-
#        agnostic and can be used across many contexts.
#
# Revision History:
# Date        Author            Change Description
# 9/12/2020   cgarcia           Initial version.
# 9/29/2020   cgarcia           Added threshold acceptance class.
# 9/30/2020   cgarcia           Updated find_time_insert_node to include random start time generation.
#-----------------------------------------------------------------------------------------------------

import os
import time
import json
import random as rnd
import util_data as du
from structs import *


        
# ========== Adaptive Large Neighborhood Search-Related Code =========================================

# This class represents a mutable solution representation for ALNS for this problem.
class ALNSEncodedSolution:
    def __init__(self, problem, job_nodes=None, assigned_node_ids=[], objective_f_val=0):
        self.job_nodes = []
        if job_nodes == None:
            self.job_nodes = [build_node_object(problem, i) for i in job_node_inds(problem)]
        else:
            self.job_nodes = [j.clone() for j in job_nodes]
        self.job_node_dict = dict([(j.node_id, j) for j in self.job_nodes])
        self.assigned_node_ids = list(assigned_node_ids)
        self.problem = problem
        self.objective_f_val = objective_f_val
        
    def clone(self):
        return ALNSEncodedSolution(self.problem, self.job_nodes, self.assigned_node_ids, self.objective_f_val)

# Tries to insert a job node into an assignment set by finding a feasible time. The time
# search divides the time window into discrete points time_delta apart and tries 
# sequentially to find one point that is feasible.
# @param job_node: a Node object
# @param assignment_set: an AssignmentSet object
# @param time_delta: the distance between starting time points to try
# @param randomize_start_times: True | False OR int
#                               If True or False, whether to randomize the start time search order.
#                                 - If False, goes in earliest-time-first order.
#                               If int, the number of randomly-generated time points within the time window to try.
# @returns: True or False, depending on whether or not a time could be found to insert the node.
# NOTE: This will have the side-effect of modifying the job_node start time if successfully inserted.
def find_time_insert_node(job_node, assignment_set, time_delta, randomize_start_times=False):
    original_t = job_node.start_time
    st_candidates = [job_node.openw, job_node.closew]
    if type(randomize_start_times) == type(1):
        st_candidates = [du.rand_float(job_node.openw, job_node.closew) for i in range(randomize_start_times)]
    else:
        st_candidates = du.segment_to_points(job_node.openw, job_node.closew, time_delta) 
        if randomize_start_times:
            rnd.shuffle(st_candidates)
    for t in st_candidates:
        j = job_node.clone()
        job_node.start_time = t
        success = assignment_set.insert_node(job_node)
        if success:
            return True
    job_node.start_time = original_t
    return False

# This method simply takes an encoded solution and builds its corresponding AssignmentSet object.
# @param encoded_sol: an ALNSEncodedSolution object
# @returns: an AssignmentSet object
def decode(encoded_sol):
    asmts = AssignmentSet(encoded_sol.problem)
    for j_ind in encoded_sol.assigned_node_ids:
            asmts.insert_node(encoded_sol.job_node_dict[j_ind])
    return asmts

# Builds a repair function of form {ALNSEncodedSolution} -> {ALNSEncodedSolution} 
# @param job_node_order_f: A function of form [{Node}] -> [{Node}] to order the job nodes to be added
# @param time_delta: the distance between starting time points to try
# @param randomize_start_times: True or False, whether to randomize the start time search order.
#                               If False, goes in earliest-time-first order.
# @returns: a repair function that sequentially adds nodes in the order given, attempting
#           to find an appropriate start time. 
def build_repair_f(job_node_order_f, time_delta, randomize_start_times):
    def repair_f(encoded_sol):
        next_sol = encoded_sol.clone()
        asmts = AssignmentSet(encoded_sol.problem)
        next_sol.job_nodes = job_node_order_f(next_sol.job_nodes)
        tabu = set()
        for j_ind in next_sol.assigned_node_ids:
            node = next_sol.job_node_dict[j_ind]
            asmts.insert_node(node)
            tabu = tabu.union(node.conflict_ids)
        for j in next_sol.job_nodes:
            if not(j.node_id in tabu) and not(j.node_id in next_sol.assigned_node_ids):
                success = find_time_insert_node(j, asmts, time_delta, randomize_start_times)
                if success:
                    tabu = tabu.union(j.conflict_ids)
        next_sol.assigned_node_ids = asmts.get_scheduled_node_ids()        
        next_sol.objective_f_val = asmts.reward
        return next_sol
    return repair_f

# Builds a destroy function of form {ALNSEncodedSolution} -> {ALNSEncodedSolution} 
# @param job_node_order_f: A function of form [{Node}] -> [{Node}] to order the job nodes to be added       
# @param min_frac: the minimum fraction of nodes to remove
# @param max_frac: the maximum fraction of nodes to remove  
# @returns: a destroy function that sequentially removes nodes in the order given, attempting
#           to find an appropriate start time.   
def build_destroy_f(job_node_order_f, min_frac, max_frac):
    def destroy_f(encoded_sol):
        next_sol = encoded_sol.clone()
        next_sol.job_nodes = job_node_order_f(next_sol.job_nodes)
        assigned_node_ids = list(next_sol.assigned_node_ids)
        n = int(round(du.rand_float(min_frac, max_frac) * len(assigned_node_ids)))
        nodes = [j for j in next_sol.job_nodes if j.node_id in assigned_node_ids][:n]
        for j in nodes:
            next_sol.objective_f_val -= j.reward
            next_sol.assigned_node_ids.remove(j.node_id)
        return next_sol
    return destroy_f


# ========== Generic Adaptive Large Neighborhood Search Code =========================================
# All code below can be used in a generic manner apart from any specific problem.

# This is the base class for acceptance method classes. Classes are needed because
# state needs to be maintained as the iterations increase.
class AcceptanceMethodBase:
    def __init__(self):
        raise 'AcceptanceMethodBase is an abstract class - please implement'
        
    def accept(self, s_curr, s_next, cost_f):
        raise 'AcceptanceMethodBase.accept is an abstract method - please implement'

# The old bachelor method decreses the threshold separately depending on whether 
# an accept or reject is encountered.
class OldBachelorAccept(AcceptanceMethodBase):
    def __init__(self, T_init, accept_decrease_factor, reject_decrease_factor):
        self.T = T_init
        self.accept_decrease_factor = accept_decrease_factor
        self.reject_decrease_factor = reject_decrease_factor
    
    def accept(self, s_curr, s_next, cost_f):
        acpt = False
        if cost_f(s_next) - cost_f(s_curr) < self.T:
            acpt = True
            self.T *= (1 - self.accept_decrease_factor)
        else:
            self.T *= (1 - self.reject_decrease_factor)
        return acpt

# This class uses exponential cooling like simulated annealing, but rather than temperature
# it simply sarts with an initial probability of acceptance of worse solution and decreases
# this probability by a constant factor each iteration.
class ExponentialDecreasingProbAccept(AcceptanceMethodBase):
    def __init__(self, initial_p=0.5, decrease_factor=0.98):
        self.current_p = initial_p
        self.decrease_factor = decrease_factor
        
    def accept(self, s_curr, s_next, cost_f):
        acpt = False
        if cost_f(s_next) < cost_f(s_curr) or rnd.random() < self.current_p:
            acpt = True
        self.current_p *= self.decrease_factor
        return acpt

# This class is threshold acceptance based on the new solution cost being within a 
# threshold percent of the current solution.
class ThresholdAccept(AcceptanceMethodBase):
    def __init__(self, initial_threshold_frac=0.25, decrease_factor=0.99):
        self.current_threshold_frac = initial_threshold_frac
        self.decrease_factor = decrease_factor
        
    def accept(self, s_curr, s_next, cost_f):
        acpt = False
        if cost_f(s_next) < (1.0 + self.current_threshold_frac) * cost_f(s_curr):
            acpt = True
        self.current_threshold_frac *= self.decrease_factor
        return acpt
        
# This provides ALNS weight updating corresponding to a set of repair or destroy founctions.
# @param weights: the current set of weights
# @param points: the accumulated points for each function
# @param attempts: the number of attempts for each function
# @param reaction_factor: the lambda parameter
# @returns: an updated set of weights
def updated_weights(weights, points, attempts, reaction_factor):
    w = []
    for i in range(len(weights)):
        w.append((1 - reaction_factor) * weights[i])
        if attempts[i] > 0:
            w[i] += reaction_factor * (float(points[i]) / float(attempts[i]))
    return w
            
# This provides a generic implementation of Adaptive Large Neighborhood Search.
# @param initial_sol: an initial solution  
# @param max_iter: max number of iterations
# @param max_unimprove_time: max number of seconds without improvement allowed.
# @param reaction_factor: the reaction factor
# @param cost_f: a cost function to use as a solution comparison basis. Of form f:{solution} -> {number}  
# @param accept_method: a subclass of AcceptanceMethodBase
# @param update_period: the number of iterations per period for updating weights
# @param repair_fs: a list of repair functions of form f:{solution} -> {solution}
# @param repair_fs: a list of destroy functions of form f:{solution} -> {solution}
# @param weight_deltas: 4 elements: e[0] > e[1] > e[2] > e[3], prividing reward points
#                       corresponding to the 4 improvement conditions of interest.
# @returns: a dict of form {'solution':<ALNSEncodedSolution>, 'cost':<cost>, 'elapsed_time':<time>}
def alns(initial_sol, max_iter, max_unimprove_time, reaction_factor, cost_f,
         accept_method, update_period, repair_fs, destroy_fs, weight_deltas):
    repair_weights = [1 for i in range(len(repair_fs))]
    destroy_weights = [1 for i in range(len(destroy_fs))]
    repair_points = [0 for i in range(len(repair_fs))]
    destroy_points = [0 for i in range(len(destroy_fs))]
    repair_attempts = [0 for i in range(len(repair_fs))]
    destroy_attempts = [0 for i in range(len(destroy_fs))]
    curr_iter = 1
    last_improve_time = time.time()
    start_time = last_improve_time
    best_sol = initial_sol
    current_sol = best_sol
    while curr_iter <= max_iter and time.time() <= last_improve_time + max_unimprove_time:
        if curr_iter % update_period == 0:
            repair_weights = updated_weights(repair_weights, repair_points, repair_attempts, reaction_factor)
            destroy_weights = updated_weights(destroy_weights, destroy_points, destroy_attempts, reaction_factor)
            repair_points = [0 for i in range(len(repair_fs))]
            destroy_points = [0 for i in range(len(destroy_fs))]
            repair_attempts = [0 for i in range(len(repair_fs))]
            destroy_attempts = [0 for i in range(len(destroy_fs))]
            print('Iteration ' + str(curr_iter) + ':, best cost=' + str(cost_f(best_sol)) + ', elapsed_time=' + str(time.time() - start_time))
        ri = du.random_weighted_index(repair_weights)
        di = du.random_weighted_index(destroy_weights)
        repair_attempts[ri] += 1
        destroy_attempts[di] += 1
        next_sol = repair_fs[ri](destroy_fs[di](current_sol))
        accepted = accept_method.accept(current_sol, next_sol, cost_f)
        if cost_f(next_sol) < cost_f(best_sol):
            repair_points[ri] += weight_deltas[0]
            destroy_points[di] += weight_deltas[0]
            best_sol = next_sol
            last_improve_time = time.time()
        elif cost_f(next_sol) < cost_f(current_sol):
            repair_points[ri] += weight_deltas[1]
            destroy_points[di] += weight_deltas[1]
        elif accepted:
            repair_points[ri] += weight_deltas[2]
            destroy_points[di] += weight_deltas[2]
        else:
            repair_points[ri] += weight_deltas[2]
            destroy_points[di] += weight_deltas[2]
        if accepted:
            current_sol = next_sol
        curr_iter += 1
    return {'solution':best_sol, 'cost':cost_f(best_sol), 'elapsed_time':time.time() - start_time}    
    
    