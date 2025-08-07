#!/usr/bin/env bash

# Download and install CARLA
mkdir carla_server
cd carla_server
wget https://carla-releases.b-cdn.net/Linux/CARLA_0.9.15.tar.gz
wget https://carla-releases.b-cdn.net/Linux/AdditionalMaps_0.9.15.tar.gz
tar -xf CARLA_0.9.15.tar.gz
tar -xf AdditionalMaps_0.9.15.tar.gz
rm CARLA_0.9.15.tar.gz
rm AdditionalMaps_0.9.15.tar.gz
cd ..
