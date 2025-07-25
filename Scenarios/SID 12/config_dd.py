import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =   [
   361560459127309953,
        18382962346800043259,
        6555489296698433922,
        14999302206072972801,
        13168640789758914183,
        14867477969409060360,
        3036892023549020046,
        14459546260613332876,
        7783727404168196753,
        8446940798543044114,
        1761858368787216790,
        6634999638885201556,
        16803589194738102290,
        12822359035617286165,
        2558378127059596316,
        10435276304034077723,
        15855467729382517662,
        15091970582448281122,
        12217631557311595817,
        6043762930284665134,
        9142204588599488045,
        5519350855301838766,
        947391780994026163,
        972297587807810996,
        1406470589011057076,
        9926936965828814512,
        11622163645485395506,
        16539277387185671089,
        2585862824805875512,
        7110969549648213943,
        17714362728608496047,
        14924629716111278776,
        18247149166612365893,
        6485923076015119437,
        53880962673747408,
        14746789883701736394,
        10482165454295825357,
        13577937716950948811,
        7482725249379275218,
        10878077605309499090,
        8555468678682883540,
        2923417064712112475,
        11951164071266389852,
        13390595512284494685,
        18125725892881901402,
        1621944113982735076,
        9994454871908136289,
        6556381045547962851,
        1823174588307572325,
        8380202814765138789,
        7709090443345717475,
        12344756517730691174,
        13642685646239287400,
        9564112102409119595,
        2519343175636707824,
        6616653381866928495,
        1694366188340096626,
        12924430986578757618,
        15680281095858937460,
        8793436644587297784,
        2630081664371749371
    ]
    

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =[
      387,
        20,
        21,
        22,
        23,
        155,
        157,
        160,
        161,
        162,
        291,
        420,
        292,
        293,
        167,
        448,
        196,
        74,
        75,
        77,
        346,
        484,
        485,
        114,
        115,
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
