import json
import subprocess
import time
import os

# Define constants for PASS and FAIL
PASS = 0  # Able to recreate the same scenario
FAIL = 1  # Failed to recreate the same scenario

# Define various lists of entities that can be manipulated in the simulation
building_ids = [
    6624907388525486529, 5590853173915701067, 11595376130058892747,
    11261989655324469416, 10827724883280509631, 18345568482389893230,
    1580899482231826983, 1760263306195875505, 12193930106007007199,
    8965582157476607102, 2012950392265273169, 8202849075528332341,
    6570133562374327036, 8588501765608435261, 3725429243769496776,
    12942124512259043244, 4899373996816986076, 7783727404168196753,
    1601677913125771255, 4983866454221917867, 793883526509223864,
    11096794554960802340, 18125725892881901402, 9314362118298296807,
    10311091484298245286, 12405707544884411272, 14597101749787311194,
    1437529571490662170, 160167791312577125, 12317005202958092029,
    2630081664371749371, 2795511079265638899, 17619596962267012938,
    12253574462247490343, 3709560905934411224
]

traffic_light_ids = [97, 98, 99, 100]

weather_time_conditions = ['rain', 'fog', 'cloudy', 'night']

streetlight_ids = [
    73, 72, 71, 70, 69, 68, 61, 50, 40, 24, 26, 25, 27, 130, 456, 440, 305, 301, 
    347, 122, 165, 166, 211, 212, 215, 217, 218, 242, 243, 244, 312, 323, 334, 
    344, 343, 345, 162, 163, 164, 241, 306, 307, 346
]

# Delta debugging algorithm
def ddmin(test, inp, *test_args):
    assert test(inp, *test_args) != FAIL  # Ensure the input causes failure initially
    
    n = 2  # Initial granularity: start by dividing the input into two parts
    step_count = 1  # Counter for logging steps
    print("Step | Subsequence                              | Error Triggered")
    print("------------------------------------------------------------")
    while len(inp) >= 2:
        start = 0  # Starting index for the current subset
        subset_length = len(inp) // n  # Length of each subset
        some_complement_is_failing = False   # Flag to check if any complement passes

        while start < len(inp):
            # Create a complement by excluding the current subset
            complement = inp[:start] + inp[start + subset_length:]
            # Test the complement
            error_triggered = test(complement, *test_args) == PASS
            # Log the step
            print(f"{step_count:<5} | {complement}{' '*(40-len(str(complement)))}| {'PASS' if error_triggered else 'FAIL'}")
            step_count += 1  # Increment step count here
            if error_triggered:
                # If the complement passes (error is still triggered), reduce the input
                inp = complement
                n = max(n - 1, 2)  # Decrease granularity to check smaller subsets
                some_complement_is_failing = True
                break

            start += subset_length  # Move to the next subset

        if not some_complement_is_failing:
            # If no complement failed, increase granularity
            if n == len(inp):
                break  # If n equals the input length, exit the loop
            n = min(n * 2, len(inp))  # Double the granularity, but do not exceed input length

    return inp  # Return the minimized input


def test_function(inp): 
    # Test whether a given input configuration causes a collision in a simulation
    try:
        collision_rate = get_collision_rate(inp)  # Get the collision rate
        return PASS if collision_rate > 0 else FAIL
    except Exception as e:
        print(f"Error during test: {e}")
        return FAIL


def get_collision_rate(inp):
    # Calculate the collision rate for a given input configuration
    with open('test_input.json', 'w') as f:
        json.dump(inp, f)
        
    npc_count = 4 if 'Four NPCs' in inp else 2
    script_name = "run_generation_transfuser.sh" if npc_count == 4 else "run_generation_transfusers.sh"

    try:
        # Start the Carla server
        os.system("gnome-terminal -- bash -c 'cd carla_server; ./CarlaUE4.sh; exec bash'")
        time.sleep(5)  # Wait for the server to start

        # Run the appropriate script with the npc_count argument
        result = subprocess.run(["bash", script_name], capture_output=True, text=True)
        output = result.stdout

        collision_rate = None
        for line in output.splitlines():
            if "Collision rate:" in line:
                collision_rate = float(line.split("Collision rate:")[1].strip())
                break

        if collision_rate is None:
            raise ValueError("Collision rate not found in output")
    except Exception as e:
        print(f"Error parsing collision rate: {e}")
        return 0.0
    finally:
        os.system("pkill -f CarlaUE4")  # Stop the Carla server

    return collision_rate


if __name__ == "__main__":
    initial_test_input = building_ids + traffic_light_ids + streetlight_ids + weather_time_conditions + ['Bike', 'Pedestrian', 'Four NPCs']
    
    while len(initial_test_input) > 1:
        print(f"Initial Test Input Length: {len(initial_test_input)}")
        print(f"Initial Test Input: {initial_test_input}")
        
        # Perform delta debugging to find the minimal failure-inducing input
        minimal_input = ddmin(test_function, initial_test_input)

        # Print the minimal failure-inducing input
        print(f"Minimal failure-inducing input: {minimal_input}")
        
        if not minimal_input:
            break  # Exit if no minimal input is found

        # Remove the first entity of the minimal subset
        entity_to_remove = minimal_input[0]
        print(f"Removing entity: {entity_to_remove}")
        
        # Create the new initial test input by removing the entity from the whole initial test input
        initial_test_input = [entity for entity in initial_test_input if entity != entity_to_remove]
        
        print(f"New Test Input Length: {len(initial_test_input)}")
        print(f"New Test Input: {initial_test_input}")
        
        if len(initial_test_input) == 0:
            break  # Exit if all entities have been removed
