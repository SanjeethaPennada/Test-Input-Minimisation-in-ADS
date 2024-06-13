import carla
import random
import json

#Define various lists of entities that can be manipulated in the simulation
#Define the building ids that should be removed in the selected scenario (Town 3, 197 route ID) 
building_ids = [6624907388525486529, 5590853173915701067, 11595376130058892747, 11261989655324469416, 10827724883280509631, 18345568482389893230, 1580899482231826983, 1760263306195875505, 12193930106007007199, 8965582157476607102, 2012950392265273169, 8202849075528332341, 6570133562374327036, 8588501765608435261, 3725429243769496776, 12942124512259043244, 4899373996816986076, 7783727404168196753, 1601677913125771255, 4983866454221917867, 793883526509223864, 11096794554960802340, 18125725892881901402, 9314362118298296807, 10311091484298245286, 12405707544884411272, 14597101749787311194, 1437529571490662170, 160167791312577125, 12317005202958092029, 2630081664371749371, 2795511079265638899, 17619596962267012938, 12253574462247490343, 3709560905934411224]

 #Define the traffic light IDs that should be removed in the selected scenario
traffic_light_ids = [97, 98, 99, 100] 

# Define the weather and time conditions that should be incorporated in the selected scenario
weather_time_conditions = ['rain', 'fog', 'cloudy', 'night']  


# List of street light IDs that should be turned off in the selected scenario
streetlight_ids = [73, 72, 71, 70, 69, 68, 61, 50, 40, 24, 26, 25, 27, 130, 456, 440, 305, 301, 347, 122, 165, 166, 211, 212, 215, 217, 218, 242, 243, 244, 312, 323, 334, 344, 343, 345, 162, 163, 164, 241, 306, 307, 346]

def set_weather_time_conditions(world, weather_time_conditions):

    #Sets the weather and time conditions in the CARLA simulation.

    #Args:
    #world (carla.World): The CARLA world object.
    #weather_time_conditions (list): List of weather and time conditions to set.
    
    #Returns:
    #None

    
    weather = carla.WeatherParameters()
    
    # Default weather settings
    weather.precipitation = 0.0
    weather.precipitation_deposits = 0.0
    weather.wind_intensity = 0.20
    weather.fog_density = 0.0
    weather.fog_distance = 0.0
    weather.fog_falloff = 0.0
    weather.cloudiness = 90.0
    weather.sun_azimuth_angle = 135
    weather.sun_altitude_angle = 35
    
    # Adjust settings based on conditions
    if 'rain' in weather_time_conditions:
        weather.precipitation = 30.0
        weather.precipitation_deposits = 50.0
        weather.wind_intensity = 50.40

    if 'fog' in weather_time_conditions:
        weather.fog_density = 0.8
        weather.fog_distance = 50.0
        weather.fog_falloff = 2.0

    if 'cloudy' in weather_time_conditions:
        weather.cloudiness = 20.0

    if 'night' in weather_time_conditions:
        weather.sun_azimuth_angle = 270.0
        weather.sun_altitude_angle = -80.0

    world.set_weather(weather)

def get_street_lights(world):

    #Retrieves all street lights in the CARLA world.

    #Args:
    #world (carla.World): The CARLA world object.
    
    #Returns:
    #list: List of street light objects.
  
    
    lmanager = world.get_lightmanager()
    all_lights = lmanager.get_all_lights()
    street_lights = [light for light in all_lights if light.light_group == carla.LightGroup.Street]
    return street_lights

def turn_off_lights_by_ids(lights, streetlight_ids):

    #Turns off the street lights by their IDs.

    #Args:
    #lights (list): List of all lights in the CARLA world.
    #streetlight_ids (list): List of street light IDs to be turned off.
    
    #Returns:
    #None

    
    for light in lights:
        if light.id in streetlight_ids:
            light.turn_off()

def spawn_bike(world, spawn_location=carla.Location(x=-20.679825, y=-140.884156, z=0)):

    #Spawns a bike at the specified location in the CARLA world.

    #Args:
    #world (carla.World): The CARLA world object.
    #spawn_location (carla.Location, optional): The location to spawn the bike. Defaults to a predefined location.
    
    #Returns:
    #carla.Actor: The spawned bike actor, or None if no bike blueprint is available.
   
    
    blueprint_library = world.get_blueprint_library()
    bike_blueprints = blueprint_library.filter('vehicle.harley-davidson.low_rider')
    if bike_blueprints:
        bike_bp = random.choice(bike_blueprints)
        bike = world.spawn_actor(bike_bp, carla.Transform(spawn_location))
        return bike
    else:
        print("No bike blueprints available.")
        return None

def spawn_pedestrian(world, spawn_location=carla.Location(x=-20.599852, y=-120.541729, z=0.792587), target_location=carla.Location(x=-40.599852, y=-140.541729, z=0.792587)):

    #Spawns a pedestrian and sets a target location for them to walk to in the CARLA world.

    #Args:
    #world (carla.World): The CARLA world object.
    #spawn_location (carla.Location, optional): The location to spawn the pedestrian. Defaults to a predefined location.
    #target_location (carla.Location, optional): The target location for the pedestrian to walk to. Defaults to a predefined location.
    
    #Returns:
   # tuple: The spawned pedestrian actor and its controller actor.

    
    blueprint_library = world.get_blueprint_library()
    walker_bp = random.choice(blueprint_library.filter('walker.pedestrian.*'))
    pedestrian = world.spawn_actor(walker_bp, carla.Transform(spawn_location))
    
    pedestrian_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
    pedestrian_controller = world.spawn_actor(pedestrian_controller_bp, carla.Transform(), attach_to=pedestrian)
    
    pedestrian_controller.start()
    pedestrian_controller.go_to_location(target_location)
    
    return pedestrian, pedestrian_controller

def configure_environment(inp):

   # Configures the CARLA simulation environment based on the input configuration.

    #Args:
    #inp (list): List of entities and conditions to be applied in the simulation.
    
    #Returns:
    #None
  
    
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.load_world('Town03')

    # Remove specified buildings
    for building_id in building_ids:
        if building_id in inp:
            world.enable_environment_objects({building_id}, False)
            print(f"Building with ID {building_id} has been removed.")
            
    #Remove specified tarffic lights
    for traffic_light_id in traffic_light_ids:
        if traffic_light_id in inp:
            traffic_light = world.get_actor(traffic_light_id)
            if traffic_light:
                traffic_light.destroy()
                print(f"Traffic light with ID {traffic_light_id} has been removed.")

    #Set weatherand time conditions
    relevant_conditions = [condition for condition in weather_time_conditions if condition in inp]
    if relevant_conditions:
        set_weather_time_conditions(world, relevant_conditions)
    
    # Turn off specified street lights
    street_lights = get_street_lights(world)
    for light_id in streetlight_ids:
        if light_id in inp:
            turn_off_lights_by_ids(street_lights, [light_id])
            print(f"Street light with ID {light_id} has been turned off.")

    # Spawn a bike if specified
    if 'Bike' in inp:
        spawn_bike(world)
        
    # Spawn a pedestrian if specified
    if 'Pedestrian' in inp:
        spawn_pedestrian(world)

    world.tick()

if __name__ == "__main__":

    # Load test input from JSON file
    with open('test_input.json', 'r') as f:
        test_input_from_file = json.load(f)

    # Print the test input loaded from file
    print(f"Test Input from file: {test_input_from_file}")

    # Configure the environment based on the test input
    configure_environment(test_input_from_file)
