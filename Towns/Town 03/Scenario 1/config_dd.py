import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =[
        14667240896428621566,
        14585871644390627070,
        6985771807368227206,
        12151133131409843844,
        15730254308531548549,
        14097615817170731653,
        8950187907806240648,
        15258374943793249418,
        17235122108563265677,
        6030282197145637780,
        17627136342559728660,
        9392071419933920155,
        10556292272449826464,
        13033434228184466849,
        6579379009551399333,
        4541376302780397737,
        16470533959264367652,
        15844954996823609767,
        12495691760231386670,
        10199914373438228143,
        10649589213450182065,
        8794281533802726069,
        14108779543167826866,
        16152256174392885045,
        17588387645644995256,
        3561252634485631611,
        16936932519825465789,
        15238124405572899009,
        10188087204226691652,
        2146880334852567369,
        16553804302339654005,
        863696338541212363,
        6030763135588007373,
        8732043879944152783,
        16313181619495315148,
        7787089966138231893,
        10574521412553297749,
        1309893919863712474,
        5436003053874918619,
        6119766853874817756,
        18238141741817433176,
        1840917525183906911,
        15291547881600329180,
        15953077761112880349,
        16547936984919951199,
        8176918256333549158,
        12261070413986386661,
        5506737825174028137,
        7989182760411716713,
        17798064116822404580,
        11645801049091093097,
        6286168434174988653,
        16411497468756660201,
        7819788032457275244,
        9644659433010866921,
        7434222945297012083,
        16549561832190754160,
        3723439850461389687,
        7481202552286640118,
        11649272373429102199,
        1562699237605548669
    ]
    

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =[
        387,
        20,
        21,
        150,
        22,
        23,
        162,
        291,
        420,
        292,
        293,
        167,
        178,
        179,
        183,
        185,
        186,
        187,
        188,
        189,
        190,
        191,
        448,
        449,
        450,
        451,
        193,
        195,
        452,
        194,
        196,
        199,
        197,
        200,
        204,
        198,
        201,
        207,
        74,
        465,
        466,
        75,
        77,
        346,
        484,
        485,
        498
    ]
# Define the weather and time conditions
def set_weather_time_conditions(world, weather_conditions):
    """Sets weather and time conditions in CARLA based on the input conditions."""
    weather = carla.WeatherParameters()

    # Time conditions
    if 'morning' in weather_conditions:
        weather.sun_azimuth_angle = 180.0
        weather.sun_altitude_angle = 30.0
    else:  # night
        weather.sun_azimuth_angle = 270.0
        weather.sun_altitude_angle = -80.0

    # Precipitation conditions
    if 'dry' in weather_conditions:
        weather.precipitation = 0.0
        weather.precipitation_deposits = 0.0
        weather.wind_intensity = 10.0
    else:  # wet
        weather.precipitation = 30.0
        weather.precipitation_deposits = 50.0
        weather.wind_intensity = 50.40

    # Fog conditions
    if 'clear' in weather_conditions:
        weather.fog_density = 2.0
        weather.fog_distance = 0.75
        weather.fog_falloff =  0.10000000149011612
    else:  # fog
        weather.fog_density = 10.0
        weather.fog_distance = 50.0
        weather.fog_falloff = 2.0

    world.set_weather(weather)

def get_street_lights(world):
    """Retrieves all street lights in the CARLA world."""
    lmanager = world.get_lightmanager()
    all_lights = lmanager.get_all_lights()
    return [light for light in all_lights if light.light_group == carla.LightGroup.Street]

def turn_off_lights_by_ids(lights, streetlight_ids):
    """Turns off the street lights by their IDs."""
    for light in lights:
        if light.id in streetlight_ids:
            light.turn_off()



def configure_environment(inp):
    """Configures the CARLA simulation environment based on the input configuration."""
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.load_world('Town03')



    # Debug building removal
    print(f"Input received: {inp}")
    print(f"Defined building_ids: {building_ids}")
    has_buildings = any(bid in inp for bid in building_ids)
    print(f"Any building IDs found in input: {has_buildings}")
    
    
    if not has_buildings:
        print("No building IDs found, attempting to remove all buildings...")
        try:
            building_set = set(building_ids)
            print(f"Building set to remove: {building_set}")
            world.enable_environment_objects(building_set, False)
            print(f"All buildings ({len(building_ids)} total) removed successfully.")
            # Verify removal
            active_objects = world.get_environment_objects(carla.CityObjectLabel.Building)
            print(f"Buildings remaining after removal: {len(active_objects)}")
        except Exception as e:
            print(f"Error removing buildings: {e}")
    else:
        print("Building IDs found, removing only unspecified ones...")
        for building_id in building_ids:
            if building_id not in inp:
                try:
                    world.enable_environment_objects({building_id}, False)
                    print(f"Building with ID {building_id} has been removed.")
                except Exception as e:
                    print(f"Error removing building {building_id}: {e}")
                    
    # Debug streetlight handling
    print(f"Defined streetlight_ids: {streetlight_ids}")
    has_streetlights = any(sid in inp for sid in streetlight_ids)
    print(f"Any streetlight IDs found in input: {has_streetlights}")
    street_lights = get_street_lights(world)
    
    if not has_streetlights:
        try:
            turn_off_lights_by_ids(street_lights, streetlight_ids)
            print(f"All streetlights ({len(streetlight_ids)} total) turned off as no streetlight IDs were specified in input.")
        except Exception as e:
            print(f"Error turning off all streetlights: {e}")
    else:
        for light_id in streetlight_ids:
            if light_id not in inp:
                try:
                    turn_off_lights_by_ids(street_lights, [light_id])
                    print(f"Street light with ID {light_id} has been turned off.")
                except Exception as e:
                    print(f"Error turning off streetlight {light_id}: {e}")
    # Weather conditions
    weather_conditions = []
    if 'morning' in inp:
        weather_conditions.append('morning')
    else:
        weather_conditions.append('night')
    if 'dry' in inp:
        weather_conditions.append('dry')
    else:
        weather_conditions.append('wet')
    if 'clear' in inp:
        weather_conditions.append('clear')
    else:
        weather_conditions.append('fog')

    set_weather_time_conditions(world, weather_conditions)

    world.tick()

if __name__ == "__main__":
    # Load test input from JSON file
    with open('test_input.json', 'r') as f:
        test_input_from_file = json.load(f)
    
    # Print the test input loaded from file
    print(f"Test Input from file: {test_input_from_file}")
    
    # Configure the environment based on the test input
    configure_environment(test_input_from_file)

#pkill -9 gnome-terminal
