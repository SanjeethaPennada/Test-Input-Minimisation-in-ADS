# An Empirical Comparison of Input Minimisation Algorithms for ADS Scenario Simplification (DD Vs ProbDD Vs CDD)

This repository contains the code to automatically compare state-of-the-art test-input minimisation algorithms such as Delta Debugging (DD), Probabilistic DD (ProbDD) and Counter DD (CDD) for Scenario simplification in Autonomous Driving Systems (ADS). If you find this repository useful, please cite. 

## Contents
1. [Prerequisites](#Prerequisites)
2. [Setup](#setup)
3. [DD Vs ProbDD Vs CDD for ADS Scenario Simplification](#DD-Vs-ProbDD-Vs-CDD-for-ADS-Scenario-Simplification)
   
## Prerequisites

### Hardware
- GPU: NVIDIA Corporation
- Memory: 16GB+
- Storage: 100GB+

### Software
- Ubuntu 20.04
- nvidia driver
- CARLA 0.9.15

## Setup
Clone the repo
```Shell
git clone https://github.com/SanjeethaPennada/Test-Input-Minimisation-in-ADS.git
cd Test-Input-Minimisation-in-ADS
```

### Environment
Install drivers and reboot. If the appropriate version of the driver is already installed(Check with the command `nvidia-smi`), you can skip this step.
```Shell
sudo apt update
sudo apt install ubuntu-drivers-common
sudo ubuntu-drivers autoinstall
sudo reboot
```

Install anaconda and build the environment.
```Shell
wget https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh
bash Anaconda3-2022.05-Linux-x86_64.sh
source ~/.profile
conda env create -f environment.yml
conda activate king
```

### CARLA
Download and setup CARLA 0.9.15.
```Shell
chmod +x setup_carla.sh
./setup_carla.sh
```
![alt text](https://github.com/SanjeethaPennada/Test-Input-Minimisation-in-ADS/blob/main/Images/CARLA.png)

Make sure to install all the required packages from [requirements.txt](https://github.com/SanjeethaPennada/Test-Input-Minimisation-in-ADS/blob/main/requirements.txt)

### Transfuser
To generate scenarios for [TransFuser](https://github.com/autonomousvision/transfuser), you need to download the model weights:
```Shell
mkdir -p driving_agents/king/transfuser/model_checkpoints/regular
cd driving_agents/king/transfuser/model_checkpoints/regular
wget https://s3.eu-central-1.amazonaws.com/avg-projects/transfuser/models.zip
unzip models.zip
rm -rf models.zip late_fusion geometric_fusion cilrs aim
cd -
```

### Initial checks before running the code
Please make sure the "CARLA_ROOT" ("./carla_server" by default) and "Test-Input-Minimisation-in-ADS_ROOT" (if present), the environment variables are set correctly in all the bash scripts. The following script will compare different test-input minimisation algorithms for scenario simplification in ADS. 

## DD Vs ProbDD Vs CDD for ADS Scenario Simplification
#### Example: Scenario ID 3
1. Go to carla_server folder, where CarlaUE4.sh is present and run:
   ```Shell
   conda activate king
   ./CarlaUE4.sh 
   ```
2. Go to the root folder, and run:
```Shell
bash run_generation_transfuser.sh
```
This initialises a failure scenario at a T-junction involving a head-on collision.

3. In Scenarios folder, we have different python files corresponding to each and every scenario.

   a. subset_20perTown.xml -- this generates the road where the scenario needs to be executed, so based on the Scenario ID i.e., SID  this needs to be changed in 
      https://github.com/SanjeethaPennada/Test-Input-Minimisation-in-ADS/tree/main/leaderboard/data/routes. 

   b. NPC.zip -- extract this folder into NPC.json and this contains the pre-defined path that NPCs has to follow.

   c. config_dd.py -- this contains the set of building ids, street light ids, weather conditions, time conditions that needs to configured during scenario              simplification.

    d. algorithms.py -- this automatically runs scenario simplification using all the three test-input minimisation algorithms using strong oracle. For weak              oracle, two lines within get_collision_rate(inp) function needs to be changed as below
      - python3 collisiontype.py to python3 collision.py and
      - "Head-on" in output to "Accident" in output

4. Therefore, since we are trying to simplify Scenario ID 3, we need to get all these python files into the root folder and run: 
```Shell
python3 algorithms.py
```
This runs scenario simpliication in ADS using DD, ProbDD and CDD for initial test input: npc_ids +  weather_time_conditions + building_ids + streetlight_ids. Repeat this for different test input combinations for both oracles: 
- weather_time_conditions + npc_ids + streetlight_ids + building_ids,
- building_ids + npc_ids + streetlight_ids + weather_time_conditions,
- streetlight_ids  + weather_time_conditions + npc_ids +  building_ids, and
- building_ids + streetlight_ids  + weather_time_conditions + npc_ids.

Compute all the three different metrics: efficiency (Avg number of steps i.e., number of simulations), effectiveness (size of the minimised input) and diversity (Number of unique solutions) 

#### Note
The CARLA simulator and bash scripts are automated to streamline the testing process. Each test input triggers the CARLA simulator to launch, complete its simulation, and then relaunch for the next input. This automated approach is necessary due to several factors: modifying test inputs and configuring the CARLA simulation environment can sometimes slow down or cause interruptions, such as the simulator stopping, closing unexpectedly, or causing system instability that requires restarting the desktop. 

Additionally, an important consideration is that the traffic light configurations change each time the world is loaded without closing CARLA. To maintain consistency and avoid issues with the changing of traffic light IDs, it's preferable to reload CARLA for each test input. Although one possible solution is to access traffic light IDs based on their location, but still remaining drawbacks prevail. Therefore, the decision was made to reload CARLA for every test input to ensure reliable and consistent simulation results.

## Acknowledgements
This implementation is based on code from several repositories. We sincerely thank the authors for their awesome work.
- [CARLA Leaderboard](https://github.com/carla-simulator/leaderboard)
- [Scenario Runner](https://github.com/carla-simulator/scenario_runner)
- [KING](https://github.com/autonomousvision/king/tree/main)
- [Toward a Better Understanding of Probabilistic Delta Debugging](https://zenodo.org/records/14425530)
- [Transfuser](https://github.com/autonomousvision/transfuser)
- [Learning by Cheating](https://github.com/dotchen/LearningByCheating)
- [World on Rails](https://github.com/dotchen/WorldOnRails)

