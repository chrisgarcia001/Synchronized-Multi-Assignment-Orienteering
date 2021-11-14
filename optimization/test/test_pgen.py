import os
import sys
sys.path.insert(1, '../core')

from structs import *
from problem_gen import *
from algorithms import *

window_param = {"step_size":30,  "max_size":240, "min_start":30, "max_end":450}
for i in range(10):
    print(random_window(window_param))
    
pgen_param_file = '../test-params/by_hand/base_prob_gen_test_1.json'
#problem_folder = '../test-data/'
problem_folder = 'C:/Users/Administrator/Desktop/opl/dynamic-multiskill-team-orienteering/data/v2.1/'

params = {}
with open(pgen_param_file, 'r') as infile:
    params = json.load(infile)
    
#pg = ProblemSetGenerator(params)
pg = ProblemGeneratorBase(params)
#pg = ProblemGeneratorWithCosts(params)
prob = pg.generate()
prob.to_opl_file(problem_folder + 'v2.1_test_1.dat')
#print(pg.generate())