# Synchronized Multi-Assignment Orienteering
Problems, solutions, and algorithms for the Synchronized Multi-Assignment Orienteering Problem. 

This repository contains source code, benchmark problem sets, and solutions for research on the Synchronized 
Multi-Assignment Orienteering Problem. This repository is organized as follows:

1. Core Source Code

The core source code is found in the *optimization* folder. This contains all core models, algorithms, and running infrastructure.
The main code is in Python 3. The MIP model is implemented using OPL and used with the CPLEX solver. You will need both of these
installed to be able to use this code and run the experiments.

2. Benchmark Problems

Benchmark problems are found in the *problems* folder. There is also a readme in that folder which provides more details on the
problem format.

3. Computational Experiments and Results

The different computational experiment results and main scripts are found in the folders having prefix *experiment*.

4. Algorithm Tuning

The algorithm tuning code used to determine the main paramter values is found in the folder *tuning-factorial*.

#### Paper and Citation

The full paper can be found [here](https://www.aimsciences.org/article/doi/10.3934/jimo.2022018). If you wish to cite this work, please use the following reference: 

Garcia, C. (2023), "The synchronized multi-assignment orienteering problem", *Journal of Industrial and Management Optimization*, 19(3):1790-1812.
