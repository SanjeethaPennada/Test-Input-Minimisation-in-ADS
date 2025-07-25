import carla
import json
import os

# Define various lists of entities that can be manipulated in the simulation

# Define entities that can be manipulated in the simulation
building_ids =   [
  14629083126418030590,
        12044691803723055623,
        11787230782715619853,
        16249365206454237195,
        10524282694208318484,
        4990921837289591321,
        14415130445061220374,
        13682437728760514584,
        16887196612155340823,
        5365658124388683805,
        15046929213216099359,
        10843952666397045793,
        5526699101654839333,
        16806868381472798751,
        12215923361026932776,
        17150913427873212966,
        3740906564190154284,
        12495691760231386670,
        12382831330667386415,
        13849945566840305199,
        14545609827858096178,
        984531414431178308,
        14323467047825696831,
        14724389718272911423,
        11375386848259744832,
        2484650683583877705,
        10944871636349280329,
        553336168711390803,
        14260382128454729806,
        6152357290997665370,
        1840917525183906911,
        4428826972742246495,
        9625298279031795291,
        15504585032343404639,
        8759686939644524643,
        17755514505869882463,
        8176918256333549158,
        11645801049091093097,
        8083786122614449263,
        4687515420348263031,
        1562699237605548669,
        11732188704403739769,
        6958315545574823548,
        6599157963354147460,
        17605158174447176836,
        12496842162389383821,
        1273653098034431123,
        6432541834932299922,
        17235122108563265677,
        16186209201407313554,
        8223934525506136217,
        11415255042173040792,
        2661338064383788189,
        17560626991655729319,
        8072835138550753452,
        3670187631272361134,
        7762665143441393836,
        10199914373438228143,
        12266203196460257454,
        8794281533802726069,
        5238057263115307703,
        13939520498437195445,
        12078131182523114168,
        17475296379880973499,
        13820588846531928767,
        8167058584016693954,
        15238124405572899009,
        9510000523093073609,
        13518946051787357386,
        8323587211028569294,
        8732043879944152783,
        16313181619495315148,
        1309893919863712474,
        12261070413986386661,
        9600090438672914153,
        2787361543575081199,
        15282366474488082155,
        7880905633739802351,
        12740515991975753969,
        4593551479207885563,
        6104543018473576193,
        15407330551144689921,
        11302300036802702085,
        7032373181792815366,
        4864804515467129098,
        15737085178123335430,
        1645911225909649688,
        13813312462682639650,
        5344815380947694886,
        8480431953392606504,
        6514095914585850669,
        17267652342373700911,
        9079601028819634996,
        14296769888808808242,
        12481717351552901938,
        16152256174392885045,
        6197096724272461116,
        9608007272875567931,
        6139975750507333448,
        4604006333330424137,
        10322437638966093127,
        12268002719898572616,
        4932649977950198601,
        374504254492218192,
        12086686027909790032,
        6296819417829721943,
        17760334406089631573,
        17375226849935201624,
        11825076767809190749,
        16003504632672611165,
        7163339591923479905,
        12992265346355791711,
        8866738546483557729,
        9048112478154102623,
        13294177301177361765,
        9321473667010108263,
        3640266726395249515,
        16723804405178321254,
        5506737825174028137,
        16450635686025597802,
        5137500351520999792,
        13725883985223258990,
        13686071092872147315,
        4406556482947455355,
        16553804302339654005,
        9588893588573876609,
        12114179282472363398,
        5227126492445849998,
        8104127134131416466,
        4912923282932965273,
        14836321169981662108,
        11431439876557050271,
        2426856128320948644,
        6579379009551399333,
        2986529683977740202,
        15844954996823609767,
        11482994972927240106,
        7236970622029314987,
        10553693741256470958,
        5433768364331453362,
        10649589213450182065,
        18104486075086832559,
        11411500431478922680,
        18151811547478754741,
        9490097917423573432,
        15185986500752298423,
        18302541309294182842,
        10138450464556999615,
        17960218237713351102,
        8645966189909333956,
        3289943016631938504,
        10888068353317610949,
        16491570393976167878,
        6030763135588007373,
        12689337117691487696,
        3746263829671719894,
        16575173394337365969,
        107554107361481176,
        8351388965014716886,
        17798064116822404580,
        4908027782056315882,
        4681809741947632111,
        9337363127694677489,
        11128530166464526833
    ]
    

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =[
          132,
        133,
        394,
        395,
        397,
        144,
        401,
        406,
        408,
        153,
        410,
        412,
        413,
        414,
        415,
        159,
        417,
        418,
        163,
        164,
        165,
        301,
        305,
        306,
        307,
        308,
        311,
        312,
        313,
        440,
        317,
        192,
        323,
        334,
        471,
        472,
        473,
        474,
        343,
        344,
        345,
        222,
        223,
        347,
        346
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
