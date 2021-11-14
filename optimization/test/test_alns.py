import os
import pprint
import sys
sys.path.insert(1, '../core')

import util_data as du

from structs import *
from problem_gen import *
from alns import *

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
#prob.to_opl_file(opl_problem_folder + 'ga_test_problem.dat')
#prob.to_json_file(json_problem_folder + 'ga_test_problem.json')


# ---- ALNS Config -----
# Function Form Example:
#alns(initial_sol, max_iter, max_unimprove_time, reaction_factor, cost_f,
#         accept_method, update_period, repair_fs, destroy_fs, weight_deltas):

# Node orderings
best_first = lambda x: sorted(x, key=lambda y:-y.reward)
worst_first = lambda x: sorted(x, key=lambda y:y.reward)
most_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.time_window_length()) / float(y.ptime)))
least_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.ptime) / float(y.time_window_length())))
randomized = lambda x: du.shuffled(x)

time_delta = 5
min_frac, max_frac = 0.2, 0.5

initial_sol = ALNSEncodedSolution(prob)
max_iter = 1000
max_unimprove_time = 8
reaction_factor = 0.25
cost_f = lambda x: -x.objective_f_val
accept_method = ExponentialDecreasingProbAccept(0.75, 0.95)
update_period = 100

# build_repair_f(job_node_order_f, time_delta, randomize_start_times)
repair_fs = [build_repair_f(best_first, time_delta, True),
             build_repair_f(best_first, time_delta, 15),
             build_repair_f(best_first, time_delta, False),
             build_repair_f(most_rigid_first, time_delta, True),
             build_repair_f(most_rigid_first, time_delta, False),
             build_repair_f(randomized, time_delta, True)]
             
# build_destroy_f(job_node_order_f, min_frac, max_frac)
destroy_fs = [build_destroy_f(worst_first, min_frac, max_frac),
              build_destroy_f(least_rigid_first, min_frac, max_frac),
              build_destroy_f(randomized, min_frac, max_frac)]

weight_deltas = [0, 1, 2, 3]

sol = alns(initial_sol, max_iter, max_unimprove_time, reaction_factor, cost_f,
           accept_method, update_period, repair_fs, destroy_fs, weight_deltas)

print('Objective Function Value: ' + str(sol['solution'].objective_f_val))