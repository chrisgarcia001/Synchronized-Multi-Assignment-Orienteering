#-----------------------------------------------------------------------------------------------------
# Author: cgarcia@umw.edu
# Created: 9/12/2020
# About: This file provides uniform wrappers for each algorithm. Each algorithm wrapper takes a 
#        BaseProblem and param dict as input and returns a solution as a dict in the form:
#        {'solution':<json-able dict containing solution attributes>, 'objective_f':<obj>, 'elapsed_time':time}
#
# Revision History:
# Date        Author            Change Description
# 9/12/2020   cgarcia           Initial version.
#-----------------------------------------------------------------------------------------------------

import alns
import ga
from structs import *
from functools import reduce

# Converts an ordered list of Nodes and a corresponding AssignmentSet object 
# to a json-writable/readable solution in the following form:
# [{'worker':<worker id>, 'job_node':<job node id>, 'role':<role id>, 'start_time':<job start time>}]
def generic_solution_to_dict(job_nodes, assignment_set):
    aset = assignment_set
    assigned_job_nodes = [a for a in job_nodes if a.node_id in aset.scheduled_node_ids]
    a = reduce(lambda x,y: x+y, [[{'job_node':j.node_id, 'start_time':j.start_time, 'worker':a[0], 'role':a[1]} 
                                  for a in aset.node_assignment_dict[j.node_id]] for j in assigned_job_nodes] + [[]])
    return {'assignments':a, 'reward':aset.reward}

# This method applies ALNS to the problem using the given parameters.    
def alns_algorithm(prob, params):
    initial_sol = alns.ALNSEncodedSolution(prob)
    max_iter = params['max_iter']
    max_unimprove_time = params['max_unimprove_time']
    reaction_factor = params['reaction_factor']
    cost_f = params['cost_f']
    accept_method = params['accept_method']
    update_period = params['update_period']
    repair_fs = params['repair_fs']
    destroy_fs = params['destroy_fs']
    weight_deltas = params['weight_deltas']
    initial_sol = sorted([r(alns.ALNSEncodedSolution(prob)) for r in repair_fs], key=lambda x:cost_f(x))[0] # Start with best initial solution.
    sol = alns.alns(initial_sol, max_iter, max_unimprove_time, reaction_factor, cost_f,
                    accept_method, update_period, repair_fs, destroy_fs, weight_deltas)
    job_nodes = sol['solution'].job_nodes
    asmt = alns.decode(sol['solution'])
    return {'solution':generic_solution_to_dict(job_nodes, asmt), 
            'objective_f':asmt.reward, 'elapsed_time':sol['elapsed_time']}        
            
