# Automated Scenario Simplification 

## Requirements

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
git clone https://github.com/SanjeethaPennada/King-Replay.git
cd king
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
![alt text](https://github.com/SanjeethaPennada/Scenario__Simplification/blob/main/Images/CARLA.png)

Make sure to install all the required packages from [requirements.txt](https://github.com/SanjeethaPennada/Scenario__Simplification/blob/main/requirements.txt)

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
Please make sure the "CARLA_ROOT" ("./carla_server" by default) and "KING_ROOT" (if present) environment variables are set correctly in all the bash scripts. The following script will generate a scenario with modifications, calculates the collision rate, and based on this rate, simplifies the scenario using a delta debugging algorithm and finds the true minimum set of scenario entities required to induce the same failure as original scenario. 

## How to run
The `generate_scenarios.py` script configures the environment using settings from `config.py`. The config.py configures the CARLA simulation environment based on the input configuration obtained from dd.py, the delta debugging algorithm. Initially, `dd.py` receives an initial test input that includes all specified IDs (entire sequence). The delta debugging algorithm within `dd.py` automatically launches the CARLA simulator, executes bash scripts based on the number of agents specified in the input sequence, and generates a scenario under the configured environment settings. It then computes the "collision_rate". If the collision rate is greater than 0, indicating successful recreation of the scenario, the delta debugging algorithm returns PASS. If the collision rate is 0, indicating a failure to recreate the scenario, it returns FAIL. Upon detecting an error, the algorithm tests the complement of the input. If the complement successfully passes, it reduces granularity and continues this process until it identifies the minimum set of entities that reproduce the failure. Conversely, if the complement fails, it increases granularity and repeats the process until achieving a PASS. This iterative refinement continues until the algorithm identifies the smallest set of inputs that reliably reproduce the original scenario's failure. Each minimized test input iteration is stored in `test_input.json`. This file configures subsequent runs of the CARLA simulation environment for further testing by the delta debugging algorithm, which verifies the collision_rate. The process persists until the minimum set of entities causing the original failure is identified. 

#### Note
The CARLA simulator and bash scripts are automated to streamline the testing process. Each test input triggers the CARLA simulator to launch, complete its simulation, and then relaunch for the next input. This automated approach is necessary due to several factors: modifying test inputs and configuring the CARLA simulation environment can sometimes slow down or cause interruptions, such as the simulator stopping, closing unexpectedly, or causing system instability that requires restarting the desktop. 

Additionally, an important consideration is that the traffic light configurations change each time the world is loaded without closing CARLA. To maintain consistency and avoid issues with the changing of traffic light IDs, it's preferable to reload CARLA for each test input. Although one possible solution is to access traffic light IDs based on their location, but still remaining drawbacks prevail. Therefore, the decision was made to reload CARLA for every test input to ensure reliable and consistent simulation results.

#### Run dd.py 
The `dd.py` script concurrently executes `generate_scenario.py`, `config.py`, and bash scripts specific to the chosen scenario. It then returns the minimized input shown below. 

![alt text](https://github.com/SanjeethaPennada/Scenario__Simplification/blob/main/Images/output.png)

If slight chnages are made in the order of weather_time conditions, then the output of DD algorithm also varied. 

![alt text](https://github.com/SanjeethaPennada/Scenario__Simplification/blob/main/Images/output%202.png)




