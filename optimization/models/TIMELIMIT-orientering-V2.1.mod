/*********************************************
 * OPL 12.10 Model
 * Author: cgarcia
 * Creation Date: Aug 19, 2020 at 2:36:50 AM
 *********************************************/

 /* Node Matrix Format:
    Nodes 1 to numWorkers are Origin nodes
    Nodes (numWorkers + 1) to (numNodes - numWorkers) are Job nodes
    Nodes (numNodes - numWorkers) to numNodes are Destination nodes
 */
 
 execute PARAMS {
   cplex.tilim = 1200; // time limit in seconds
 }


 int numWorkers = ...;
 int numRoles = ...;
 int numNodes = ...;
 range Workers = 1..numWorkers;
 range Roles = 1..numRoles;
 range Nodes = 1..numNodes;
 range JobNodes = (numWorkers + 1)..(numNodes - numWorkers);
 range NodesPlus = (numWorkers + 1)..numNodes;
 range NodesMinus = 1..(numNodes - numWorkers);
 float wStart[Nodes] = ...;
 float wEnd[Nodes] = ...;
 float p[Nodes] = ...;
 int d[Roles][JobNodes] = ...;
 int e[Workers][Roles] = ...;
 float r[JobNodes] = ...;
 float g[JobNodes][JobNodes] = ...;
 float t[Nodes][Nodes] = ...;
 float M = ...;
 
 dvar int+ x[Workers][Nodes][Nodes] in 0..1; 
 dvar int+ y[JobNodes] in 0..1; 
 dvar int+ u[Workers][Roles][JobNodes] in 0..1; 
 dvar float+ s[Nodes]; 
 
 maximize sum(j in JobNodes) (r[j] * y[j]);
 
 constraints {
   forall(h in Workers, k in JobNodes) {
 	  sum(j in NodesMinus) x[h][j][k] == sum(j in NodesPlus) x[h][k][j]; // constraint 2
 	  forall(i in Roles) u[h][i][k] <= e[h][i]; // constraint 3
 	  sum(i in Roles) u[h][i][k] == sum(j in NodesMinus) x[h][j][k]; // constraint 5
 	  sum(j in NodesMinus) x[h][j][k] <= y[k];  // constraint 6	    
    }  
    	 
    forall (i in Roles, j in JobNodes) {
 	  sum(h in Workers) (e[h][i] * u[h][i][j]) == d[i][j] * y[j]; // constraint 4
    }
    
    forall(h in Workers, k in Nodes) { 
 	  forall(j in Nodes) { 
 	    s[k] >= s[j] + p[j] + (t[j][k] * x[h][j][k]) - (M *  (1 - x[h][j][k])); // constraint 7
      } 	     
  	} 	
  	  
    forall(j in Nodes) wStart[j] <= s[j] <= wEnd[j]; // constraint 8 
    forall(j in JobNodes) sum(k in JobNodes) g[j][k] * y[k] <= M * (1 - y[j]); // constraint 9  
    forall(h in Workers) {
      sum(j in NodesPlus) x[h][h][j] == 1; // constraint 10
      sum(j in NodesMinus) x[h][j][numNodes - numWorkers + h] == 1; // constraint 11
    } 
    forall(h, i in Workers, j in Nodes: h != i) x[h][i][j] == 0;  // constraint 12
 }   
 