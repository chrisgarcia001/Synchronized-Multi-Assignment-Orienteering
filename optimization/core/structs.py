#-----------------------------------------------------------------------------------------------------------
# Author: cgarcia@umw.edu
# Created: 8/21/2020
# About: This file contains some component structures and core representations
#
# Revision History:
# Date        Author            Change Description
# 8/21/2020   cgarcia           Initial version.
# 9/9/2020    cgarcia           Adding in core objects and AssignmentSet class
# 10/6/2020   cgarcia           Added sorting in Assignment set by worker qualification counts (line 202).
#-----------------------------------------------------------------------------------------------------------

import json
from functools import *

class BaseProblem:
    def __init__(self, num_workers=0, num_roles=0, num_nodes=0, windows=[], ptimes=[], M=9999999999.9,
                 worker_role_qualifications=[], demands=[], rewards=[], job_conflicts=[], travel_times=[]):
        self.num_workers = num_workers
        self.num_roles = num_roles
        self.num_nodes = num_nodes  
        self.w = windows                    # all nodes
        self.p = ptimes                     # all nodes
        self.e = worker_role_qualifications # [workers][roles]
        self.d = demands                    # [roles][job nodes]
        self.r = rewards                    # job nodes
        self.g = job_conflicts              # [job nodes][job nodes]
        self.t = travel_times               # [all nodes][all nodes]
        self.M = M
        
        
    def to_dict(self):
        return {'num_workers':self.num_workers, 'num_roles':self.num_roles, 'num_nodes':self.num_nodes, 
                'w':self.w, 'p':self.p, 'e':self.e, 'd':self.d, 'r':self.r, 'g':self.g, 't':self.t, 'M':self.M}
    
    def to_json_file(self, output_filename):
        with open(output_filename, 'w') as outfile:
            json.dump(self.to_dict(), outfile)
    
    def from_dict(self, dct):
        self.num_workers = dct['num_workers']
        self.num_roles = dct['num_roles']
        self.num_nodes = dct['num_nodes']
        self.w = dct['w']
        self.p = dct['p']
        self.e = dct['e']
        self.d = dct['d']
        self.r = dct['r']
        self.g = dct['g']
        self.t = dct['t']
        self.M = dct['M']
        
    def from_json_file(self, input_filename):
        with open(input_filename, 'r') as infile:
            self.from_dict(json.load(infile))

    def to_opl(self):
        s = 'M = ' + str(self.M) + ";\n"
        s += 'numWorkers = ' + str(self.num_workers) + ";\n"
        s += 'numRoles = ' + str(self.num_roles) + ";\n"
        s += 'numNodes = ' + str(self.num_nodes) + ";\n"
        s += 'wStart = ' + str([w[0] for w in self.w]) + ";\n"
        s += 'wEnd = ' + str([w[1] for w in self.w]) + ";\n"
        s += 'p = ' + str(self.p) + ";\n"
        s += 'e = ' + str(self.e) + ";\n"
        s += 'd = ' + str(self.d) + ";\n"
        s += 'r = ' + str(self.r) + ";\n"
        s += 'g = ' + str(self.g) + ";\n"
        s += 't = ' + str(self.t) + ";\n"
        return s
        
    def to_opl_file(self, output_filename):
        with open(output_filename, 'w') as outfile:
            outfile.write(self.to_opl())
            
                    
# ---------------------------------- Algorithm Prerequisite Structures and Functions -----------------

class Node:
    def __init__(self, node_id, openw, closew, demands=[], 
                 ptime=0, reward=0, conflict_ids=[], start_time=None):
        self.node_id = node_id
        self.openw = openw
        self.closew = closew
        self.demands = list(demands)
        self.ptime = ptime
        self.reward = reward
        self.conflict_ids = list(conflict_ids)
        self.start_time = openw if start_time == None else start_time
        
    def clone(self):
        return Node(self.node_id, self.openw, self.closew, self.demands, 
                    self.ptime, self.reward, self.conflict_ids, self.start_time)
                    
    def get_time_window(self):
        return (self.openw, self.closew)
        
    def time_window_length(self):
        return self.closew - self.openw
    
class Worker:
    def __init__(self, worker_id, qualifications, source_node_id, dest_node_id):
        self.worker_id = worker_id
        self.qualifications = list(qualifications)
        self.source_node_id = source_node_id
        self.dest_node_id = dest_node_id
        
    def clone(self):
        return Worker(self.worker_id, self.qualifications, self.source_node_id, self.dest_node_id)
 

# ---------- Some basic access and object construction functions ----
def get_worker_objects(problem):
    span = problem.num_nodes - problem.num_workers
    return [Worker(i, problem.e[i], i, i + span) for i in range(problem.num_workers)]
        
def build_node_object(problem, i):
    jr = range(problem.num_workers, problem.num_nodes - problem.num_workers)
    span = problem.num_workers
    demands = [problem.d[r][i-span] for r in range(problem.num_roles)] if i in jr else [0 for r in range(problem.num_roles)]
    conflicts = [j for j in jr if i in jr and j in jr and problem.g[i-span][j-span] == 1]
    reward = problem.r[i-span] if i in jr else 0
    return Node(i, problem.w[i][0], problem.w[i][1], demands, problem.p[i], reward, conflicts)
                
def source_node_inds(problem):
    return list(range(problem.num_workers))
    
def job_node_inds(problem):
    return list(range(problem.num_workers, problem.num_nodes - problem.num_workers))
    
def dest_node_inds(problem):
    return list(range(problem.num_workers + problem.num_jobs, problem.num_nodes))
    
def get_job_node_objects(problem):
    return [build_node_object(problem, j) for j in range(job_node_inds(problem))]


# This class keeps track of inserted nodes and worker assignments as a solution is constructed.
class AssignmentSet:
    # Constructs this AssignmentSet object from the specified problem.
    # param problem: a Problem object.
    def __init__(self, problem=None):
        workers = []
        nodes = []
        transp_matrix = []
        if problem != None:
            workers = get_worker_objects(problem)
            nodes = [build_node_object(problem, i) for i in range(problem.num_nodes)]
            transp_matrix = problem.t
        self.construct_from_objects(workers, nodes, transp_matrix)
            
    # Constructs this AssignmentSet object from the specified objects.
    # @param workers: a list of Worker  objects.
    # @param nodes: a complete list of Node objects (i.e. source, job, and destination nodes). 
    # @param transp_matrix: a |nodes| x |nodes| matrix consisting of travel times from each node id i to j.
    def construct_from_objects(self, workers=[], nodes=[], transp_matrix=[]):
        self.worker_dict = dict([(w.worker_id, w) for w in workers]) # a dict of form {worker_id:<worker object>}
        self.worker_qualification_counts = dict([(w.worker_id, sum(w.qualifications)) for w in workers])  # a dict of form {worker_id:<count>}
        self.node_dict = dict([(n.node_id, n) for n in nodes])       # a dict of form {node_id:<node object>}
        self.transp_matrix = transp_matrix                           # a matrix containing travel times from each node id i to j
        
        # A dict of form {(node_id_1, node_id_2): [worker_id_1, worker_id_2, ...]}
        self.arc_workers_dict = dict([((w.source_node_id, w.dest_node_id), [w.worker_id]) for w in workers])
        
        source_assignments = [(w.source_node_id, [(w.worker_id, None)]) for w in workers]
        dest_assignments = [(w.dest_node_id, [(w.worker_id, None)]) for w in workers]
        self.node_assignment_dict = dict(source_assignments + dest_assignments) # a dict of form {node_id:[(worker_id, assigned role)]}
        self.scheduled_node_ids = [] # A list of the node ids that have been successfully scheduled, in the order they were scheduled.
        self.reward = 0  # The total accumulated reward for all nodes inserted/assigned
    
    # Gets a list viable arcs where the node can be inserted between, together with total slack resulting.
    # @param new_node_id: a node_id to be inserted
    # @returns: a list in form [((from_node_id, to_node_id), slack)]
    def viable_insertion_arcs(self, new_node_id):
        es = set(self.arc_workers_dict.keys())
        nd = self.node_dict
        t = self.transp_matrix
        j = new_node_id
        viable = []
        for (i, k) in es:
            slack_ij = nd[j].start_time - (nd[i].start_time + nd[i].ptime + t[i][j])
            slack_jk = nd[k].start_time - (nd[j].start_time + nd[j].ptime + t[j][k])
            if min(slack_ij, slack_jk) >= 0:
                viable.append(((i,k), slack_ij + slack_jk))
        return viable
     
    # Attepts to insert the specified new node id into the schedule and assign appropriate workers.
    # @param new_node_id: a node_id to be inserted.
    # @returns: True or False, depending on whether the requested insertion was possible.
    def schedule_node_id(self, new_node_id):
        viable_arcs = [x for (x, y) in sorted(self.viable_insertion_arcs(new_node_id), key=lambda z:-z[1])] # [(i, j)] in most-slack-first order
        if len(viable_arcs) == 0:
            return False
        worker_arc_dict = dict(reduce(lambda x,y: x + y, [[(w, arc) for w in self.arc_workers_dict[arc]] for arc in viable_arcs]))
        worker_ids = reduce(lambda x,y: x + y, [self.arc_workers_dict[arc] for arc in viable_arcs])
        role_counts = [sum(x) for x in zip(*[self.worker_dict[y].qualifications for y in worker_ids])]
        demands = self.node_dict[new_node_id].demands
        rc_enumerated = sorted([(i, role_counts[i]) for i in range(len(role_counts))], key=lambda x:x[1])  
        new_assignments = []
        wids = list(worker_ids)
        for (role, _) in rc_enumerated:
            qualified = sorted([w for w in wids if self.worker_dict[w].qualifications[role] == 1], key=lambda x:self.worker_qualification_counts[x])
            if len(qualified) < demands[role]:
                return False
            used = qualified[0:demands[role]]
            wids = [x for x in wids if not(x in used)]
            new_assignments += [(wid, role) for wid in used]
        self.node_assignment_dict[new_node_id] = new_assignments
        self.reward += self.node_dict[new_node_id].reward
        for (wid, role) in new_assignments:
            arc = worker_arc_dict[wid]
            self.arc_workers_dict[arc].remove(wid)
            if len(self.arc_workers_dict[arc]) == 0:
                del self.arc_workers_dict[arc]
            if not((arc[0], new_node_id) in self.arc_workers_dict):
                self.arc_workers_dict[(arc[0], new_node_id)] = []
            if not((new_node_id, arc[1]) in self.arc_workers_dict):
                self.arc_workers_dict[(new_node_id, arc[1])] = []
            self.arc_workers_dict[(arc[0], new_node_id)].append(wid)
            self.arc_workers_dict[(new_node_id, arc[1])].append(wid)
        self.scheduled_node_ids.append(new_node_id)
        return True
    
    # Attempts to insert the specified new node object into the schedule and assign appropriate workers.
    # @param new_node: a node object to be inserted.
    # @returns: True or False, depending on whether the requested insertion was possible.
    def insert_node(self, new_node):
        self.node_dict[new_node.node_id] = new_node
        return self.schedule_node_id(new_node.node_id)
    
    # Gets a modifiable copy of the scheduled node ids.
    # @returns: a list of ids successfully scheduled in the order they were added.
    def get_scheduled_node_ids(self):
        return list(self.scheduled_node_ids)
    
    # Constructs a string representation of these assignments.
    def to_s(self):
        s = "\nReward=" + str(self.reward) + ";\n"
        s += 'Arc-Workers Dict='
        s += str(self.arc_workers_dict) + ";\n"
        s += 'Node Assignment Dict='
        s += str(self.node_assignment_dict) + ";\n\n"
        return s
    
    # Construct a copy of this AssignmentSet object.
    def clone(self):
        nas = AssignmentSet()
        nas.worker_dict = dict(self.worker_dict)
        nas.worker_qualification_counts = dict(self.worker_qualification_counts)
        nas.node_dict = dict(self.node_dict)
        nas.transp_matrix = list(self.transp_matrix)
        nas.arc_workers_dict = dict(self.arc_workers_dict)
        nas.node_assignment_dict = dict(self.node_assignment_dict)
        nas.scheduled_node_ids = list(self.scheduled_node_ids)
        nas.reward = self.reward
        return nas    
