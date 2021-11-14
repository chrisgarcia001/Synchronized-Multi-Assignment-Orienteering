# Guide to the Problem Data

### 1. Overview
This folder contains all problems used in the computational experiments. There are two problem sets:

1. Main experiment problems - found in the *problems* folder
- Problems in OPL/CPLEX format are in the folder *problems/cplex*
- Problems for ALNS are in json format in *problems/json*

2) Problems from Roozbeh et al (2020) - found in *problems-roozbeh folder#
- All are in json format
- A slightly different naming convention is used: *<label>.<number team members>_<problem number>.json*
- For example, problem *C102* with 4 team members would be named *c1.4_02.json*

### 2. Problem Generation for Main Experiment
All problems generated for the main experiment were generated using the parameters in the *pgen-params* folder. You can
regenerate a new random set by simply running the *pgen.py* file. Generate new problems types by modifying some of the 
parameter files in *pgen-params*.

### 3. Roozbeh et. al (2020) Data
The file *roozbeh_data_conversion.py* will convert data in the format provided by Roozbeh (2020) into the format
needed for the ALNS algorithm - i.e. same format as main experiments. To reconvert the data, simply run the
*roozbeh_data_conversion.py* file.

### References
1. Roozbeh, I. (2020). A solution approach to the orienteering problem with time windows and synchronisation constraints. Dataset retrieved from 
[https://www.sites.google.com/site/imanrzbh/datasets](https://www.sites.google.com/site/imanrzbh/datasets), accessed 9/17/2020.

2. Roozbeh, I., Hearne, J.W., and Pahlevani, D. (2020). A solution approach to the orienteering problem with time windows 
and synchronisation constraints, *Heliyon*, 6 (6), e04202.
