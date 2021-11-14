import sys
sys.path.insert(1, '../core')

import json
from alns import *
from structs import *
from problem_gen import *
from algorithms import *
from algorithm_runner import *

# --------------------- Generate Test Problems -------------------------------------------------
pgen_param_file = '../test-params/by_hand/test_30_20.json'
problem_folder = '../test-data/test_gen_problems'
solution_folder = '../test-data/test_json_solutions'

params = {}
with open(pgen_param_file, 'r') as infile:
    params = json.load(infile)
    
pg = ProblemSetGenerator(params)
pg.generate()

# BELOW: Comment out if you want to only generate problems, not test algorithms.
#exit()

# --------------------- Setup params -----------------------------------------------------------
best_first = lambda x: sorted(x, key=lambda y:-y.reward)
worst_first = lambda x: sorted(x, key=lambda y:y.reward)
most_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.time_window_length()) / float(y.ptime)))
best_most_rigid_first = lambda x: sorted(x, key=lambda y:(y.reward * float(y.time_window_length()) / float(y.ptime)))
least_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.ptime) / float(y.time_window_length())))
worst_least_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.ptime) / (y.reward * float(y.time_window_length()))))
randomized = lambda x: du.shuffled(x)

time_delta = 5
min_frac, max_frac = 0.2, 0.5

max_iter = 1000
max_unimprove_time = 25
reaction_factor = 0.25
cost_f = lambda x: -x.objective_f_val
accept_method = ExponentialDecreasingProbAccept(0.75, 0.95)
update_period = 100

# build_repair_f(job_node_order_f, time_delta, randomize_start_times)
repair_fs = [build_repair_f(best_first, time_delta, True),
             build_repair_f(best_first, time_delta, False),
             build_repair_f(most_rigid_first, time_delta, True),
             build_repair_f(most_rigid_first, time_delta, False),
             build_repair_f(best_most_rigid_first, time_delta, True),
             build_repair_f(best_most_rigid_first, time_delta, False),
             build_repair_f(randomized, time_delta, True)]
             
# build_destroy_f(job_node_order_f, min_frac, max_frac)
destroy_fs = [build_destroy_f(worst_first, min_frac, max_frac),
              build_destroy_f(least_rigid_first, min_frac, max_frac),
              build_destroy_f(worst_least_rigid_first, min_frac, max_frac),
              build_destroy_f(randomized, min_frac, max_frac)]

weight_deltas = [0, 2, 4, 8] #[0, 1, 2, 3]

# Create and populate the params dict.
params = {}
params['algorithm'] = alns_algorithm
params['problem_folder'] = problem_folder
params['solution_folder'] = solution_folder   # ======= COMMENT OUT IF NO SOLUTIONS NEED TO BE STORED
params['time_delta'] = time_delta
params['min_frac'], params['max_frac'] = min_frac, max_frac
params['max_iter'] = max_iter
params['max_unimprove_time'] = max_unimprove_time
params['reaction_factor'] = reaction_factor
params['cost_f'] = cost_f
params['accept_method'] = accept_method
params['update_period'] = update_period
params['repair_fs'] = repair_fs
params['destroy_fs'] = destroy_fs
params['weight_deltas'] = weight_deltas


# --------------------- Run Algorithm and Solve Problems ---------------------------------------

ar = AlgorithmRunner(params)
ar.run()