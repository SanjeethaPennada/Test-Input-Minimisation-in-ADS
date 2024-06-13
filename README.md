# Replay of "KING" 

## Requirements

### Hardware
- GPU: NVIDIA Corporation
- Memory: 16GB+
- Storage: 100GB+

### Software
- Ubuntu 20.04
- nvidia driver
- CARLA 0.9.15

Here's the [Step by step process to replay KING with modifications](https://github.com/SanjeethaPennada/King-Replay/blob/main/Step%20by%20step%20process%20to%20replay%20KING%20with%20modifications%20.pdf) 

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

### Carla
Download and setup CARLA 0.9.15.
```Shell
chmod +x setup_carla.sh
./setup_carla.sh
```
![alt text](https://github.com/SanjeethaPennada/King-Replay/blob/main/Images/CARLA.png)

Make sure to install all the required packages from [requirements.txt](https://github.com/SanjeethaPennada/King-Replay/blob/main/requirements.txt)

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

## How to run

### Scenario Replay
We provide a bash script for convenience. Please make sure the "CARLA_ROOT" ("./carla_server" by default) and "KING_ROOT" (if present) environment variables are set correctly in all of those scripts.

#### Running the code
For the generation script, first spin up a carla server in a separate shell:
```Shell
carla_server/CarlaUE4.sh
```
If you cannot separate the shell, execute the script in the background.
```Shell
nohup carla_server/CarlaUE4.sh 
```
Following script will run generation and automatically replay scenario with modifications and detect collisions. 

##### TransFuser generation
For Transfuser generation using both gradient paths, open run_generation_transfuser.sh, change number of agents to 1 or 2 or 4 based on your choice (default = 4 agents) and run:
```Shell
bash run_generation_transfuser.sh
```

#### Getting results
```Shell
generation_results_transfuser/
├── agents_4
    ├── RouteScenario_136_to_136
    │   ├── results.json
    │   └── scenario_records.json
    ...
    ├── opt.pkl
    └── opt.txt
```
### Collision detection

Collisions are detected in the scenario using Collision rate as shown below:

![alt text](https://github.com/SanjeethaPennada/King-Replay/blob/main/Images/collision_detection.png)

### Scenario Visualization
#### Running the code
First spin up a carla server in a separate shell:
```Shell
carla_server/CarlaUE4.sh 
```
Run the following script. The default directory is set to "generation_results_transfuser".
```Shell
bash run_visualization.sh generation_results_transfuser
```

#### Getting results
```Shell
generation_results_transfuser/
└── agents_4
    ├── RouteScenario_136_to_136
    │   ├── RouteScenario_136_iter_0.gif
    │   ├── results.json
    │   └── scenario_records.json
   
    ...
    ├── opt.pkl
    └── opt.txt
```

#### Replaying scenario with modifications
Open run_generation_transfuser.sh file, and use below arguments to replay scenario with modifications. 

a) --building     - to remove all buildings in the Town. <br />
b) --building_remove    - to remove specific buildings in the selected scenario. You can also particularly specify which building to be removed by making changes to the building_remove.py file.  <br />
c) --trafficlight_remove  - to remove traffic lights in the selected scenario.  <br />
d) --trafficlight_change  - to change the state of the traffic lights in the selected scenario.  <br />
e) --weather_afn          - to change weather conditions to afternoon.  <br />
f) --weather_mrng         - to change weather to morning.  <br /> 
g) --weather_rain         - to change weather to raining condition.  <br />
h) --CloudyDawn / --CloudyMorning/ --CloudyNight /--CloudyNoon / --CloudySunset / --Cloudytwilight - Set cloudy weather conditions.  <br />
i) --HardRainDawn / --HardRainMorning/ --HardRainNight/ --HardRainNoon/ --HardRainSunset/ --HardRainTwilight - Set hard rain weather conditions.  <br />
j) --MidRainDawn/ --MidRainMorning / --MidRainNight / --MidRainNoon /  --MidRainSunset  / --MidRainTwilight - Set medium rain conditions.  <br />
k) --SoftRainDawn/ --SoftRainMorning / --SoftRainNight / --SoftRainNoon / --SoftRainSunset/ --SoftRainTwilight - Set soft rain weather conditions.  <br />
l) --WetCloudyDawn/ --WetCloudyMorning / --WetCloudyNight/ --WetCloudyNoon/ --WetCloudySunset/ --WetCloudyTwilight  - Set wet cloudy weather conditions.  <br />
m) --WetDawn/ --WetMorning / --WetNight / --WetNoon / --WetSunset / --WetTwilight  - Set wet weather conditions. <br />
n) --dynamic_weather - Set dynamic weather conditions. 

#### For example, to replay scenario with modifications: 

Open run_generation_transfuser.sh file, and type below arguments to tailor the environment. Add arguments as indicated in generate_scenarios.py file.  For example if you would like to 

i) change weather to CloudyNight: Use argument –cloudy_night in run_generation_transfuser.sh, spin up CARLA and open terminal to run:
```Shell
bash run_generation_transfuser.sh
```
![alt text](https://github.com/SanjeethaPennada/King-Replay/blob/main/Images/weather.png)

The scenario is generated with cloudy_night settings. 

ii) Toggle off all the buildings in a scenario using –building argument in run_generation_transfuser.sh, then run:
```Shell
bash run_generation_transfuser.sh
```
![alt text](https://github.com/SanjeethaPennada/King-Replay/blob/main/Images/toggling.png)

iii) If you want to toggle specific building in the scenario use argument –building_remove run_generation_transfuser.sh, and select the building you want to remove by making corresponding changes to building_remove.py file. 

![alt text](https://github.com/SanjeethaPennada/King-Replay/blob/main/Images/Building.png)

#Define your location (replace these coordinates with your actual location) <br />
location = carla.Location(x=-150.0, y=30.0, z=50.0)  # to remove top left building   <br />
location = carla.Location(x=-150.0, y=70.0, z=50.0)  # to remove bottom left building  <br />
location = carla.Location(x=-80.0, y=100.0, z=100.0)  # to remove top right building   <br />
location = carla.Location(x=-80.0, y=180.0, z=120.0)  # to remove bottom right building  <br />

#Define the radius within which to search for buildings <br />
radius = 100.0  #to remove  top left building  <br />
radius = 100.0  # to remove bottom left building  <br />
radius = 150.0  # to remove top right building  <br />
radius = 200.0  # to remove bottom right building  <br />

#Collect the IDs of the first n buildings <br />
first_n_building_ids = [building.id for building in building_objects[:60]] # to remove top left building   <br />
first_n_building_ids = [building.id for building in building_objects[:100]]  #to remove bottom left building  <br />
first_n_building_ids = [building.id for building in building_objects[:10]]  # to remove top right building   <br />
first_n_building_ids = [building.id for building in building_objects[:45]] # to remove bottom right building  <br />

Then run:
```Shell
bash run_generation_transfuser.sh
```






