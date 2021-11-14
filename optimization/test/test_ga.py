import os
import pprint
import sys
sys.path.insert(1, '../core')

from structs import *
from problem_gen import *
from ga import *

pgen_param_file = '../test-params/by_hand/ga_test.json'
#json_problem_folder = '../test-data/'
opl_problem_folder = 'C:/Users/Administrator/Desktop/opl/dynamic-multiskill-team-orienteering/data/v2.1/'

params = {}
with open(pgen_param_file, 'r') as infile:
    params = json.load(infile)
    
#pg = ProblemSetGenerator(params)
pg = ProblemGeneratorBase(params)
#pg = ProblemGeneratorWithCosts(params)
prob = pg.generate()
prob.to_opl_file(opl_problem_folder + 'ga_test_problem.dat')
#prob.to_json_file(json_problem_folder + 'ga_test_problem.json')


# ---- GA Config -----
initial_pop_builder_f = initial_population_gen_pipeline([(randomized_initial_population, 0.5),
                                                         (best_reward_first_initial_population, 0.5)])
initial_pop = initial_pop_builder_f(prob, 1000)
#initial_pop = randomized_initial_population(prob, 200)


crossover_f = build_crossover_f(0.1, 0.3)

# build_mutator_f(max_swap_dist, n_swap_probs, max_start_time_change_frac, start_time_change_prob)
mutator_f = build_mutator_f(1, [0.5, 0.25, 0.25], 0.4, 0.1)
fitness_f = lambda x: objective_f(x) ** 2
max_iterations = 200
max_unimprove_time = 5
elitism_proportion = 0.05
n_jobs = 1
verbose = True
# --------------------

ga = GeneticAlgorithm(initial_pop, mutator_f, crossover_f, fitness_f, max_iterations,
                      max_unimprove_time, elitism_proportion, n_jobs, verbose)

s = initial_pop[0]
#print([x.node_id for x in s.job_nodes])
#print(construct_assignment_set(s).to_s())
sol = ga.solve()
print('Objective Function: ' + str(construct_assignment_set(sol['solution']).reward))