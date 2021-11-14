import os
import sys
sys.path.insert(1, '../optimization/core')

import json
from alns import *
from structs import *
from algorithms import *
from algorithm_runner import *
from param_optim import *


root_prob_folder = './problems'
output_filename = './reports/tuning_report_factorial.csv'


best_first = lambda x: sorted(x, key=lambda y:-y.reward)
worst_first = lambda x: sorted(x, key=lambda y:y.reward)
most_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.time_window_length()) / float(y.ptime)))
best_most_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.time_window_length()) / float((y.reward + 1) * y.ptime)))
least_rigid_first = lambda x: sorted(x, key=lambda y:(float(y.ptime) / float(y.time_window_length())))
worst_least_rigid_first = lambda x: sorted(x, key=lambda y:(y.reward * float(y.time_window_length()) / float(y.ptime)))
randomized = lambda x: du.shuffled(x)

time_delta = 5
random_starts = 50
minmax_fracs = [(0.2, 0.5)]

max_iter = [4000]
max_unimprove_time = [60]
reaction_factor = [0.25, 0.7]
cost_f = [lambda x: -x.objective_f_val]
accept_method = [ThresholdAccept(-0.5, 0.995), ThresholdAccept(-0.5, 0.998), ExponentialDecreasingProbAccept(0.75, 0.995), ExponentialDecreasingProbAccept(0.75, 0.998)]
update_period = [100]

# build_repair_f(job_node_order_f, time_delta, randomize_start_times)
repair_fs = [[build_repair_f(best_first, time_delta, True),
              build_repair_f(best_first, time_delta, False),
              build_repair_f(most_rigid_first, time_delta, True),
              build_repair_f(most_rigid_first, time_delta, False),
              build_repair_f(best_most_rigid_first, time_delta, True),
              build_repair_f(best_most_rigid_first, time_delta, False),
              build_repair_f(randomized, time_delta, True)]]
             
# build_destroy_f(job_node_order_f, min_frac, max_frac)
destroy_fs = [[build_destroy_f(worst_first, min_frac, max_frac),
               build_destroy_f(least_rigid_first, min_frac, max_frac),
               build_destroy_f(worst_least_rigid_first, min_frac, max_frac),
               build_destroy_f(randomized, min_frac, max_frac)]
               for (min_frac, max_frac) in minmax_fracs]

#min_frac, max_frac = [a for (a, b) in minmax_fracs], [b for (a, b) in minmax_fracs]

weight_deltas = [[0, 2, 4, 8], [0, 1, 2, 3]]

# Create and populate the params dict.
params = {}
params['algorithm'] = [alns_algorithm]
params['max_iter'] = max_iter
params['max_unimprove_time'] = max_unimprove_time
params['reaction_factor'] = reaction_factor
params['cost_f'] = cost_f
params['accept_method'] = accept_method
params['update_period'] = update_period
params['repair_fs'] = repair_fs
params['destroy_fs'] = destroy_fs
params['weight_deltas'] = weight_deltas


# --------------------- Run Grid Search and Optimize ---------------------------------------

gs = GridSearchParamOptimizer(params, root_prob_folder, output_filename)
gs.optimize()