import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =[
        12323576063094642555,
        8965582157476607102,
        12317005202958092029,
        12405707544884411272,
        1606541567947832463,
        7783727404168196753,
        15613097403815049616,
        15423910700219980567,
        10556292272449826464,
        1580899482231826983,
        1068051184818228267,
        12253574462247490343,
        1760263306195875505,
        12942124512259043244,
        1558447346865872567,
        8202849075528332341,
        8588501765608435261,
        10827724883280509631,
        16936932519825465789,
        3725429243769496776,
        7278641844287187398,
        2012950392265273169,
        17619596962267012938,
        12420708921766599890,
        17571360708797370448,
        4899373996816986076,
        18125725892881901402,
        15953077761112880349,
        12193930106007007199,
        15947130429781138659,
        9314362118298296807,
        9644659433010866921,
        18345568482389893230,
        7481202552286640118,
        2630081664371749371,
        8959390170926541178,
        6570133562374327036,
        6958315545574823548
    ]
# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =[
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        291,
        292,
        293,
        40,
        301,
        305,
        50,
        306,
        312,
        61,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        77,
        346,
        347,
        122,
        123,
        129,
        130,
        387,
        162,
        420,
        165,
        166,
        167,
        440,
        448,
        196,
        455,
        456,
        458,
        460,
        211,
        212,
        213,
        215,
        217,
        218,
        484,
        485,
        230,
        231,
        232,
        235,
        237,
        241,
        242,
        243,
        244,
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
