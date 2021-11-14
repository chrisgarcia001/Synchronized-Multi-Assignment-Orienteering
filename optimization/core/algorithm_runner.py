#-----------------------------------------------------------------------------------------------------
# Author: cgarcia@umw.edu
# Created: 9/12/2020
# About: This file provides a runner that can run different algorithms for uniform usage
#        and comparison.
#
# Revision History:
# Date        Author            Change Description
# 9/12/2020   cgarcia           Initial version.
#-----------------------------------------------------------------------------------------------------

import json
import os
import time
from structs import *
from algorithms import *

# -------------------------------------------- Algorithm Runner Class ------------------------------------------------------------------------------------

# This class allows the running of any algorithm found in algorithms.py which takes a set of params as input.
class AlgorithmRunner:
    def __init__(self, params):
        self.params = params
        self.algorithm = self.params['algorithm']
        self.problem_folder = self.params['problem_folder']
        self.solution_folder = self.params['solution_folder'] if 'solution_folder' in self.params else None
        self.num_replicates = self.params['replicates'] if 'replicates' in self.params else 1
        self.start_rep_numbering_at = self.params['start_rep_numbering_at'] if 'start_rep_numbering_at' in self.params else 1
    
    def run(self):
        try:
            os.makedirs(self.solution_folder)
        except:
            pass
        solutions = [] # Form: [(prob_name, [solution_rep_1, solution_rep_2, ...])]
        rep_title = lambda i: str(self.start_rep_numbering_at + i)
        for filename in [x for x in os.listdir(self.problem_folder) if x.endswith('json')]:
            try:
                replicate_solutions = []
                prob_name = filename[:len(filename) - len('.json')]
                print('Solving problem: ' + filename + '...')
                problem = BaseProblem()
                problem.from_json_file(os.path.join(self.problem_folder, filename))
                for i in range(self.num_replicates):
                    curr_replicate_filename = filename.split('.json')[0] + '___' + rep_title(i) + '.json'
                    start_time = time.time()
                    sol = self.algorithm(problem, self.params)
                    elapsed_time = time.time() - start_time
                    sol['elapsed_time'] = elapsed_time
                    sol['problem_name'] = prob_name
                    replicate_solutions.append(sol)
                    if self.solution_folder != None:
                        print('..writing to file ' + os.path.join(self.solution_folder, curr_replicate_filename))
                        with open(os.path.join(self.solution_folder, curr_replicate_filename), 'w') as outfile:
                            json.dump(sol, outfile)
                solutions.append((prob_name, replicate_solutions))
            except:
               print('Unable to read file as Problem: ' + filename)
        if self.solution_folder != None:
            print('Writing summary CSV file: ' + os.path.join(self.solution_folder, 'summary.csv') + '.....')
            rg = range(self.num_replicates)
            summary_csv_text =  ','.join(['Problem'] + ['Objective.Function_' + rep_title(i) for i in rg] + ['Elapsed.Time_' + rep_title(i) for i in rg]) 
            for pname, rep_sols in solutions:
                objs, times = [], []
                for sol in rep_sols:
                    objs.append(sol['objective_f'])
                    times.append(sol['elapsed_time'])
                summary_csv_text += "\n" + ','.join([pname] + [str(x) for x in objs] + [str(x) for x in times])   
            ri = '-' + rep_title(0) + '-' + rep_title(self.num_replicates - 1) if self.num_replicates > 1 else ''   
            with open(os.path.join(self.solution_folder, 'summary-replicates' + ri + '.csv'), 'w') as outfile:
                outfile.write(summary_csv_text)
        print('Done!')    
        return solutions
            
