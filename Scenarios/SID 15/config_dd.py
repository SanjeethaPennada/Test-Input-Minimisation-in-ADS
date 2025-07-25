import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =   [
      16072867038702838024,
        14867477969409060360,
        7783727404168196753,
        489350161739360534,
        7481202552286640118,
        10556292272449826464,
        5519350855301838766,
        1406470589011057076,
        9926936965828814512,
        17714362728608496047,
        7110969549648213943,
        3621025987161221434,
        2598729638942691901,
        16936932519825465789,
        18247149166612365893,
        11208613319949555660,
        9548445897688508247,
        2923417064712112475,
        11951164071266389852,
        18125725892881901402,
        15953077761112880349,
        17583568586570718305,
        9644659433010866921,
        6616653381866928495,
        1694366188340096626,
        943321623312612086,
        5657203444028423031,
        2630081664371749371
    ]
    

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =[
     0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        265,
        266,
        267,
        9,
        269,
        270,
        271,
        11,
        273,
        274,
        275,
        276,
        21,
        22,
        23,
        20,
        16,
        18,
        19,
        28,
        29,
        30,
        31,
        280,
        48,
        10,
        55,
        81,
        84,
        17,
        92,
        98,
        100,
        105,
        107,
        108,
        109,
        110,
        112,
        114,
        144,
        149,
        158,
        420,
        421,
        169,
        176,
        177,
        178,
        179,
        439,
        185,
        186,
        187,
        444,
        190,
        191,
        192,
        193,
        194,
        448,
        469,
        470,
        214,
        215,
        216,
        222,
        503,
        484,
        485,
        487,
        490,
        491,
        498,
        501,
        502,
        245,
        246
    ]
# Define the weather and time conditions
def set_weather_time_conditions(world, weather_conditions):
    """Sets weather and time conditions in CARLA based on the input conditions."""
    weather = carla.WeatherParameters()

    # Time conditions
    if 'morning' in weather_conditions:
        weather.sun_azimuth_angle = 170.0
        weather.sun_altitude_angle = 45.0
    else:  # night
        weather.sun_azimuth_angle = 270.0
        weather.sun_altitude_angle = -80.0

    # Precipitation conditions
    if 'dry' in weather_conditions:
        weather.precipitation = 0.0
        weather.precipitation_deposits = 0.0
        weather.wind_intensity = 5.0
    else:  # wet
        weather.precipitation = 30.0
        weather.precipitation_deposits = 50.0
        weather.wind_intensity = 50.40

    # Fog conditions
    if 'clear' in weather_conditions:
        weather.fog_density = 3.0
        weather.fog_distance = 0.75
        weather.fog_falloff =  0.8999999761581421

    else:  # fog
        weather.fog_density = 40.0
        weather.fog_distance = 60.0
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
    world = client.load_world('Town05')



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
