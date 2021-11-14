import sys
sys.path.insert(1, '../optimization/core')

import os
import random as rnd
from structs import *
from util_data import *
from problem_gen import *

def reps(pattern, n):
    return [pattern for i in range(n)]

class RoozbehProblemGenerator:
    def __init__(self, text_data, num_workers):
        nums = [int(x) for x in text_data.strip().split(' ')]
        locations = []
        i = 0
        while i < len(nums):
            locations.append(tuple(nums[i:i + 8]))
            i += 8
        self.num_workers= num_workers
        depot = locations[0]
        jobs = locations[1:]
        self.coords = [(t[1], t[2]) for t in reps(depot, num_workers) + jobs + reps(depot, num_workers) ]
        self.ptimes = reps(depot[3], num_workers) + [x[3] for x in jobs] + reps(depot[3], num_workers)
        self.rewards = [x[4] for x in jobs] 
        self.windows = reps((depot[5], depot[5]), num_workers) + [(x[5], x[6]) for x in jobs] + reps((depot[6], depot[6]), num_workers)
        self.demands = [[x[7] for x in jobs]]
        self.num_workers = num_workers
        self.qualifications = [[1] for i in range(self.num_workers)]
        self.num_nodes = (2 * num_workers) + len(jobs)
        self.num_jobs = len(jobs)
        self.M = 999999999.9
        self.wdists = [b - a for (a, b) in self.windows if b - a > 0]
        self.tdists = []
    
    def dist(self, i, j):
        c = self.coords
        dist = (((c[j][0] - c[i][0]) ** 2) + ((c[j][1] - c[i][1]) ** 2)) ** 0.5
        dp = round(dist, 2)
        if dp < round(dist, 1):
            dist = round(dist, 1) - 0.1
        else:
            dist = round(dist, 1)
        return round(dist, 1)
    
    def build_transp_matrix(self):
        M = self.M
        mat = const_matrix(self.num_nodes, self.num_nodes, 0)
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                mat[i][j] = self.dist(i, j)
                if mat[i][j] != 0: 
                    self.tdists.append(mat[i][j])
                    
        return mat
       
    def generate(self):
        conflicts = const_matrix(self.num_jobs, self.num_jobs, 0)
        return BaseProblem(self.num_workers, 1, self.num_nodes, self.windows, self.ptimes, self.M,
                           self.qualifications, self.demands, self.rewards, conflicts, 
                           self.build_transp_matrix())  

# ----- Extra utility functions -----

# Build the problem name from the filename.
def problem_name(filename, n_vehicles):
    filename = filename.split('.')[0]
    i = 0
    while i < len(filename) and not(filename[i] in [str(x) for x in list(range(10))]):
        i += 1
    if i < len(filename):
        return filename[:i + 1] + '.' + str(n_vehicles) + '_' + filename[i + 1:]
    return filename + '.' + str(n_vehicles)

# Get the percentiles for a given set of elements.
def percentile_cuts(elements, percentiles):
    ets = sorted(elements)
    return [ets[int(p * len(ets))] for p in percentiles]

# ----- Main section -----
input_folder = './roozbeh-data-raw/problems'
output_folder = './problems-roozbeh'
tdists = []
wdists = []
num_nodes = []
for filename in [x for x in os.listdir(input_folder) if x.endswith('.txt')]:
    print('Converting Problem: ' + filename + '...')
    fh = open(os.path.join(input_folder, filename))
    text = fh.read()
    fh.close()
    pg4 = RoozbehProblemGenerator(text, 4)
    pg6 = RoozbehProblemGenerator(text, 6)
    p4 = pg4.generate()
    p6 = pg6.generate()
    tdists += pg4.tdists + pg6.tdists
    wdists += pg4.wdists + pg6.wdists
    num_nodes += [len(pg4.coords), len(pg6.coords)]
    p4.to_json_file(os.path.join(output_folder, problem_name(filename, 4) + '.json'))
    p6.to_json_file(os.path.join(output_folder, problem_name(filename, 6) + '.json'))
 
print('Distance Percentiles (0%-100%): ' + str(percentile_cuts(tdists, [0.2 * i for i in range(1,5)])))
print('Time Window Percentiles (0%-100%): ' + str(percentile_cuts(wdists, [0.2 * i for i in range(1, 5)])))
print('Min/Max Time Window Lengths: ' + str(min(wdists)) + ', ' + str(max(wdists)))
print('Size Range (Num. Nodes): ' + str(min(num_nodes)) + ', ' + str(max(num_nodes)))