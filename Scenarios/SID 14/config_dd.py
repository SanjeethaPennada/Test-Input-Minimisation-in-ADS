import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =   [
   14867477969409060360,
        1116889618305068053,
        8809622762887559187,
        2756983990451087895,
        11882945622326276120,
        13682437728760514584,
        16482711477707797025,
        14821407697785722410,
        11736879144465830963,
        7060064408697210430,
        11200019682936598594,
        8098524646104364100,
        15007520672611151938,
        11578980212112180291,
        973147211554758730,
        12796637591531276868,
        18247149166612365893,
        18371458130480058954,
        14752902737895513164,
        17571360708797370448,
        5852418019762689109,
        15441250026892768339,
        16355641277105024088,
        9289832947240277083,
        1147660731562767967,
        9595241109248107621,
        6181316085581701226,
        1694366188340096626,
        4687515420348263031,
        11818128659176308854,
        11244246892030135928,
        6958315545574823548,
        7825374935844754559,
        12921170496691659903,
        11050102792789693059,
        17430176239208166530,
        7783727404168196753,
        10573848324652325017,
        10850598136167120034,
        430445683536619175,
        12061588714801024165,
        8290403131695214765,
        2851044384011188913,
        9926936965828814512,
        13779940132531667632,
        17437120396064261299,
        12758364209333863103,
        5905589260115000004,
        9734841611986342085,
        13689218654139003591,
        8732043879944152783,
        13345249968060605141,
        7742402776990929117,
        12951266613623679205,
        12261070413986386661,
        5672460169986766063,
        5640711735614635762,
        10922837648413399796,
        14343820618752614653,
        5300179916207542033,
        9660839179671372562,
        11222623585195301145,
        11444110376790416156,
        15550768920233443101,
        10198428436893413153,
        6715433680431092005,
        7760152488547340582,
        6087784096997240105,
        11611047145618137383,
        15352295894248799526,
        4660479950221006123,
        7211250189818379565,
        14779032048422240561,
        16646498508557295412,
        9017180834391418683,
        13986312903039371577,
        798088219915327806,
        10431782565840253253,
        4932649977950198601,
        541166806725841751,
        2923417064712112475,
        16611403220326390105,
        11978065467893504859,
        11951164071266389852,
        18125725892881901402,
        5506737825174028137,
        6616653381866928495,
        3570839243155466123,
        15040418923889380744,
        7870096081405458319,
        6030282197145637780,
        14150717700283944863,
        5548209316003138470,
        8164922058079997862,
        5519350855301838766,
        4257850897727666608,
        1406470589011057076,
        3460778853387730357,
        17714362728608496047,
        7110969549648213943,
        17859665951547599284,
        16725887394428541881,
        7205730509707419613,
        8148055649278279651,
        7326282221167068649,
        17817535369899937260,
        9069579346649344500,
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
        16,
        17,
        18,
        19,
        280,
        55,
        81,
        92,
        113,
        120,
        124,
        381,
        126,
        382,
        383,
        385,
        386,
        131,
        387,
        388,
        389,
        390,
        392,
        394,
        396,
        397,
        398,
        399,
        144,
        149,
        155,
        158,
        162,
        163,
        164,
        165,
        420,
        169,
        176,
        177,
        178,
        179,
        448,
        214,
        215,
        216,
        222,
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
