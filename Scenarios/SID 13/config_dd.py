import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =   [
      14867477969409060360,
        14201590550706889738,
        9567010111310794767,
        5828353549884931602,
        15960971118792443925,
        6871578278580505113,
        4124692297368912937,
        12215923361026932776,
        8202849075528332341,
        8029254863252018751,
        1858349974218384966,
        7232978153819429444,
        18247149166612365893,
        13184485960687846478,
        13645843552641462361,
        1840917525183906911,
        10582892510826019428,
        6702718770143596136,
        1694366188340096626,
        15336007771912325239,
        12793536083522245754,
        7783727404168196753,
        5086090480424316053,
        7436060146624244889,
        13861841141921254041,
        11752149690539634341,
        10199914373438228143,
        9926936965828814512,
        9991396305005058737,
        9714042697218957496,
        2261338566511865535,
        14828006460438411966,
        15689411338638923456,
        5276269753787538655,
        15468131487396859102,
        1608856132059017456,
        2506329125337804023,
        10031302706412306171,
        8073380933933678335,
        1246210916667535619,
        5732270722362656534,
        13813312462682639650,
        6168847333817040182,
        2200797522774405441,
        15040280204333862206,
        16678685206642350930,
        2923417064712112475,
        11951164071266389852,
        18125725892881901402,
        9050047291244860258,
        5036604503520396141,
        16837945488730410857,
        6616653381866928495,
        2536271810934066042,
        7103276387148171648,
        5708115672958114692,
        11905227469318655879,
        5227126492445849998,
        15940916484014944141,
        10063161584209413010,
        4652886039670997399,
        4753766400743075747,
        1675875583480061867,
        12920723826689322406,
        5519350855301838766,
        16267943605059701674,
        7444903141634653614,
        11262070243333185455,
        1406470589011057076,
        17714362728608496047,
        2158702903463018426,
        7110969549648213943,
        15365499864241953207,
        8016056896180694470,
        15807958690913182659,
        15557347493410289607,
        8932527175364071371,
        6030763135588007373,
        13993886796558280161,
        13069575999393895909,
        16205504732950409699,
        3301864024309096430,
        4681809741947632111,
        9744868703317506032,
        2630081664371749371
    ]
    

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =[
       0,
        259,
        260,
        261,
        262,
        263,
        267,
        268,
        269,
        270,
        271,
        272,
        273,
        275,
        276,
        277,
        278,
        279,
        280,
        281,
        283,
        284,
        288,
        290,
        292,
        294,
        298,
        299,
        300,
        301,
        67,
        68,
        75,
        331,
        77,
        79,
        342,
        351,
        352,
        355,
        356,
        357,
        358,
        365,
        114,
        115,
        121,
        122,
        380,
        381,
        141,
        157,
        175,
        176,
        178,
        184,
        189,
        190,
        191,
        192,
        193,
        194,
        195,
        196,
        197,
        206,
        207,
        238,
        239,
        240,
        241,
        242
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
