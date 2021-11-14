import os
import pprint
import sys
sys.path.insert(1, '../core')

from structs import *
from problem_gen import *
#from algorithms import *
#from util_test import *

window_param = {"step_size":30,  "max_size":240, "min_start":30, "max_end":450}
for i in range(10):
    print(random_window(window_param))
    
pgen_param_file = '../test-params/by_hand/base_prob_gen_test_1.json'
problem_folder = '../test-data/'
#opl_problem_folder = 'C:/Users/Administrator/Desktop/opl/dynamic-multiskill-team-orienteering/data/v2.1/'
#json_problem_folder = '../data/'

params = {}
with open(pgen_param_file, 'r') as infile:
    params = json.load(infile)
    
#pg = ProblemSetGenerator(params)
pg = ProblemGeneratorBase(params)
#pg = ProblemGeneratorWithCosts(params)
prob = pg.generate()
prob.to_opl_file(problem_folder + 'v2.1_test_1.dat')
prob.to_json_file(problem_folder + 'v2.1_test_1.json')

print(get_worker_objects(prob))
print(build_node_object(prob, 16))

# -------------- Test Assignments class ----------------
d = lambda c1, c2: (((c2[0] - c1[0])**2) + ((c2[1] - c1[1])**2))**0.5

# -- Scenario 1: Job sets (3, 4) and (3, 5) are compatible, but (4, 5) is incompatible.
print("\n ------- SCENARIO 1 -------")
workers = [] # Worker(worker_id, qualifications, source_node_id, dest_node_id)
workers.append(Worker(0, [1,0,0,1], 0, 6))
workers.append(Worker(1, [1,1,1,1], 1, 7))
workers.append(Worker(2, [0,0,1,0], 2, 8))

nodes = [] # Node(node_id, openw, closew, demands=[], ptime=0, reward=0, conflict_ids=[], start_time=None)
nodes.append(Node(0, 0, 0))
nodes.append(Node(1, 0, 0))
nodes.append(Node(2, 0, 0))
nodes.append(Node(3, 5, 10, [1,0,0,0], 2, 10, start_time=4))
nodes.append(Node(4, 3, 15, [2,0,1,0], 6, 26, start_time=13))
nodes.append(Node(5, 10, 25, [0,0,1,0], 3, 18, start_time=21))
nodes.append(Node(6, 30, 30))
nodes.append(Node(7, 30, 30))
nodes.append(Node(8, 30, 30))

locs = [(0,0), (0,0), (0,0), (2, 2), (-1, 3), (5, 2), (0,0), (0,0), (0,0)]

M = 9999999
t = [[d(locs[i], locs[j]) for j in range(len(locs))] for i in range(len(locs))]
#pprint.pprint(t)

asmt = AssignmentSet()
asmt.construct_from_objects(workers, nodes, t)
asmt = asmt.clone() # Test the clone function
print(asmt.to_s())
print(asmt.schedule_node_id(3))
print(asmt.to_s())
print(asmt.schedule_node_id(4))
print(asmt.to_s())
print(asmt.schedule_node_id(5))
print(asmt.to_s())



# -- Scenario 2: All jobs are compatible
print("\n ------- SCENARIO 2 -------")
workers = [] # Worker(worker_id, qualifications, source_node_id, dest_node_id)
workers.append(Worker(0, [1,0,0,1], 0, 6))
workers.append(Worker(1, [1,1,1,1], 1, 7))
workers.append(Worker(2, [0,0,1,0], 2, 8))

nodes = [] # Node(node_id, openw, closew, demands=[], ptime=0, reward=0, conflict_ids=[], start_time=None)
nodes.append(Node(0, 0, 0))
nodes.append(Node(1, 0, 0))
nodes.append(Node(2, 0, 0))
nodes.append(Node(3, 5, 10, [1,0,0,0], 2, 10, start_time=4))
nodes.append(Node(4, 3, 15, [2,0,1,0], 6, 26, start_time=13))
nodes.append(Node(5, 10, 25, [0,0,1,0], 3, 18, start_time=30))
nodes.append(Node(6, 50, 50))
nodes.append(Node(7, 50, 50))
nodes.append(Node(8, 50, 50))

locs = [(0,0), (0,0), (0,0), (2, 2), (-1, 3), (5, 2), (0,0), (0,0), (0,0)]

M = 9999999
t = [[d(locs[i], locs[j]) for j in range(len(locs))] for i in range(len(locs))]
#pprint.pprint(t)

asmt = AssignmentSet()
asmt.construct_from_objects(workers, nodes, t)
print(asmt.to_s())
print(asmt.schedule_node_id(3))
print(asmt.to_s())
print(asmt.schedule_node_id(4))
print(asmt.to_s())
print(asmt.schedule_node_id(5))
print(asmt.to_s())

# -- Test the construction procedure
