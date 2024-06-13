import carla
import random
import json

#Load various lists of entities that should be manipulated in the simulation from dd.py
from dd import building_ids, traffic_light_ids, weather_time_conditions, street_light_ids 

def set_weather_time_conditions(world, weather_time_conditions):

    """
    Sets the weather and time conditions in the CARLA simulation.

    Args:
    world (carla.World): The CARLA world object.
    weather_time_conditions (list): List of weather and time conditions to set.
    
    Returns:
    None
    """
    
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

    """
    Retrieves all street lights in the CARLA world.

    Args:
    world (carla.World): The CARLA world object.
    
    Returns:
    list: List of street light objects.
    """
    
    lmanager = world.get_lightmanager()
    all_lights = lmanager.get_all_lights()
    street_lights = [light for light in all_lights if light.light_group == carla.LightGroup.Street]
    return street_lights

def turn_off_lights_by_ids(lights, streetlight_ids):

    """
    Turns off the street lights by their IDs.

    Args:
    lights (list): List of all lights in the CARLA world.
    streetlight_ids (list): List of street light IDs to be turned off.
    
    Returns:
    None
    """
    
    for light in lights:
        if light.id in streetlight_ids:
            light.turn_off()

def spawn_bike(world, spawn_location=carla.Location(x=-20.679825, y=-140.884156, z=0)):

    """
    Spawns a bike at the specified location in the CARLA world.

    Args:
    world (carla.World): The CARLA world object.
    spawn_location (carla.Location, optional): The location to spawn the bike. Defaults to a predefined location.
    
    Returns:
    carla.Actor: The spawned bike actor, or None if no bike blueprint is available.
    """
    
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

    """
    Spawns a pedestrian and sets a target location for them to walk to in the CARLA world.

    Args:
    world (carla.World): The CARLA world object.
    spawn_location (carla.Location, optional): The location to spawn the pedestrian. Defaults to a predefined location.
    target_location (carla.Location, optional): The target location for the pedestrian to walk to. Defaults to a predefined location.
    
    Returns:
    tuple: The spawned pedestrian actor and its controller actor.
    """
    
    blueprint_library = world.get_blueprint_library()
    walker_bp = random.choice(blueprint_library.filter('walker.pedestrian.*'))
    pedestrian = world.spawn_actor(walker_bp, carla.Transform(spawn_location))
    
    pedestrian_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
    pedestrian_controller = world.spawn_actor(pedestrian_controller_bp, carla.Transform(), attach_to=pedestrian)
    
    pedestrian_controller.start()
    pedestrian_controller.go_to_location(target_location)
    
    return pedestrian, pedestrian_controller

def configure_environment(inp):

    """
    Configures the CARLA simulation environment based on the input configuration.

    Args:
    inp (list): List of entities and conditions to be applied in the simulation.
    
    Returns:
    None
    """
    
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
