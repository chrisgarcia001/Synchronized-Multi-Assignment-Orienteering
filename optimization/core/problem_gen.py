import os
import random as rnd
from structs import *
from util_data import *


# ----------------- PART I: UTILITY METHODS ------------------------------------------
# Example window params: {"step_size":30, "max_size":240, "min_start":30, "max_end":450}
def random_window(window_params):
    p = window_params 
    max_step_multiple = (p['max_end'] - p['min_start'] - p['step_size']) / p['step_size']
    return tuple([x * p['step_size'] for x in rand_segment(1, max_step_multiple, p['min_start']/p['step_size'], p['max_end']/p['step_size'], True)])
    

# ----------------- PART II: CORE CLASSES --------------------------------------------

class ProblemGeneratorBase:
    def __init__(self, params):
        self.num_workers = params['num_workers']
        self.num_roles = len(params['role_frequencies'])
        self.num_jobs = params['num_jobs']
        self.job_window_p = params['job_windows']
        self.worker_window_p = params['worker_windows']
        self.ptime_size_range = tuple(params['ptime_size_range'])
        self.max_time = params['max_time']
        self.role_frequencies = params['role_frequencies']
        self.job_demand_range = tuple(params['job_demand_range'])
        self.num_job_templates = params['num_job_templates']
        self.job_reward_range = tuple(params['job_reward_range'])
        self.num_multioption_jobs = params['num_multioption_jobs']
        self.depots = params['depots']
        self.max_travel_time = params['max_travel_time']
        self.correlate_reward_to_ptime = params['correlate_reward_to_ptime']
        self.M = params['M']
    
    # Build the jobs/job nodes as dict objects containing all relevant info. 
    def build_job_nodes(self):
        templates = [rand_slot_distribute(rnd.randint(*self.job_demand_range), self.num_roles) for i in range(self.num_job_templates)]
        jobs = []
        for i in range(self.num_jobs - self.num_multioption_jobs):
            template = list(rnd.choice(templates))
            window = random_window(self.job_window_p)
            ptime = rand_float(*self.ptime_size_range)
            r = rnd.randint(*self.job_reward_range) # TODO: Rework to add correlation to ptimes when needed
            jobs.append({'template':template, 'window':window, 'ptime':ptime, 'loc':(rand_float(0,1), rand_float(0,1)), 'r':r})
        mj = rnd.sample(range(len(jobs)), self.num_multioption_jobs) if self.num_multioption_jobs > 0 and len(jobs) >= self.num_multioption_jobs else []
        for j in mj:
            job = dict(jobs[j])
            job['template'] = [2 * x for x in job['template']]
            job['ptime'] /= 2.0
            job['conflict'] = j
            jobs.append(job)
        job_nodes = jobs
        if self.correlate_reward_to_ptime:
            min_ptime, max_ptime = min([j['ptime'] for j in job_nodes]), max([j['ptime'] for j in job_nodes])
            min_r, max_r = self.job_reward_range
            for j in job_nodes:
                j['r'] = min_r + ((float(j['ptime'] - min_ptime) / float(max_ptime - min_ptime)) * (max_r - min_r))
        return job_nodes
    
    # Build the worker nodes (starting/ending locations and times).
    def build_worker_nodes(self):
        workers = list(range(self.num_workers))
        rnd.shuffle(workers)
        depot_workers = [[workers.pop() for i in range(w)] for w in self.depots]
        depot_locs = [(rand_float(0, 1), rand_float(0, 1)) for depot in depot_workers]
        worker_nodes = []
        for w in workers:  # Ad-hoc workers
            worker_nodes.append({'window':random_window(self.worker_window_p), 'ptime':0, 
                                 'loc':(rand_float(0,1), rand_float(0,1)), 'type':'adhoc'})
        for depot in range(len(depot_workers)): # Depot workers
            for w in depot_workers[depot]:
                worker_nodes.append({'window':(0, self.max_time), 'ptime':0, 'loc':depot_locs[depot], 'type':'depot'})
        return worker_nodes  
    
    # Build the transportation time matrix.
    def build_transp_time_matrix(self, worker_nodes, job_nodes):
        nodes = worker_nodes + job_nodes + worker_nodes
        matrix = const_matrix(len(nodes), len(nodes), 0)
        maxd = 0
        for i in range(len(nodes)): # Compute distances
            for j in range(len(nodes)):
                matrix[i][j] = (((nodes[i]['loc'][0] - nodes[j]['loc'][0]) ** 2) + ((nodes[i]['loc'][1] - nodes[j]['loc'][1]) ** 2)) ** 0.5
                maxd = matrix[i][j] if matrix[i][j] > maxd else maxd
        for i in range(len(nodes)): # Scale
            for j in range(len(nodes)):
                matrix[i][j] = self.max_travel_time * (matrix[i][j] / maxd)
        return matrix         
    
    # Construct the conflict matrix.
    def build_conflict_matrix(self, job_nodes):
        matrix = const_matrix(len(job_nodes), len(job_nodes), 0)
        for i in range(len(job_nodes)):
            if 'conflict' in job_nodes[i]:
                j = job_nodes[i]['conflict']
                matrix[i][j] = 1
                matrix[j][i] = 1
        return matrix
    
    # The main generation method.
    def generate(self):
        qualifications = rand_bin_matrix(self.num_workers, [round(f * self.num_workers) for f in self.role_frequencies])
        job_nodes = self.build_job_nodes()
        worker_nodes = self.build_worker_nodes()
        num_nodes = len(job_nodes) + (2 * len(worker_nodes))
        
        # transp_time_matrix[Nodes][Nodes] = ...
        transp_time_matrix = self.build_transp_time_matrix(worker_nodes, job_nodes) 
        
        # g_matrix[JobNodes][JobNodes] = ...
        conflicts = self.build_conflict_matrix(job_nodes)
        
        demands = transpose([j['template'] for j in job_nodes])
        rewards = [j['r'] for j in job_nodes]
        ptimes = [0 for w in worker_nodes] + [j['ptime'] for j in job_nodes] + [0 for w in worker_nodes]
        
        windows = [(w['window'][0], w['window'][0]) for w in worker_nodes] \
                  + [j['window'] for j in job_nodes] \
                  + [(w['window'][1], w['window'][1]) for w in worker_nodes]
        # TODO: Update problem class, construct the problem object and return.
        #return transp_time_matrix #g_matrix #worker_job_cost_matrix #worker_transp_cost_matrix #transp_time_matrix #job_nodes + worker_nodes
        return BaseProblem(self.num_workers, self.num_roles, num_nodes, windows, ptimes, self.M,
                           qualifications, demands, rewards, conflicts, transp_time_matrix)  

                     

class ProblemSetGenerator:
    def __init__(self, params):
        params = self.eval_params(params)
        self.problem_generator = params['problem_generator_class'](params)
        self.problem_set_name = params['problem_set_name']
        self.num_replicates = params['num_replicates']
        self.json_output_folder = params['json_output_folder'] if 'json_output_folder' in params else None
        self.opl_output_folder = params['opl_output_folder'] if 'opl_output_folder' in params else None
    
    def eval_params(self, params):
        pms = {}
        for param in params:
            try:
                pms[param] = eval(params[param])
            except:
                pms[param] = params[param]
        return pms
    
    def generate(self):
        if self.json_output_folder != None:
            try:
                os.makedirs(self.json_output_folder)
            except:
                pass
        if self.opl_output_folder != None:
            try:
                os.makedirs(self.opl_output_folder)
            except:
                pass
        
        print('---- Generating Problem Set ' + str(self.problem_set_name) + '----')
        for i in range(self.num_replicates):
            problem = self.problem_generator.generate()
            problem_name = str(self.problem_set_name) + '_' + str(i + 1)
            if not(self.json_output_folder == None):
                print(' Writing problem to file: ' + os.path.join(self.json_output_folder, problem_name + '.json'))
                problem.to_json_file(os.path.join(self.json_output_folder, problem_name + '.json'))
            if not(self.opl_output_folder == None):
                print(' Writing problem to file: ' + os.path.join(self.opl_output_folder, problem_name + '.dat'))
                problem.to_opl_file(os.path.join(self.opl_output_folder, problem_name + '.dat'))
        print('---------------------- DONE! -------------------------------------')
        
