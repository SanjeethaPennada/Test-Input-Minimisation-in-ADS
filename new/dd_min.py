# -*- coding: utf-8 -*-
"""
Script to minimize simulation inputs causing collisions using delta debugging.
"""

import json
import subprocess
import time
import os
from typing import Callable, Sequence, Any

# Define constants for PASS and FAIL
PASS = 0  # Able to recreate the same scenario (collision rate > 0)
FAIL = 1  # Failed to recreate the same scenario (collision rate <= 0)
# Define entities that can be manipulated in the simulation
building_ids = [    14667240896428621566,
        6985771807368227206,
        15730254308531548549,
        17235122108563265677,
        6030282197145637780,
        8809622762887559187,
        9392071419933920155,
        6579379009551399333,
        15844954996823609767,
        12495691760231386670,
        10649589213450182065,
        8794281533802726069,
        14108779543167826866,
        17588387645644995256,
        3561252634485631611,
        15238124405572899009,
        10188087204226691652,
        8732043879944152783,
        16313181619495315148,
        7787089966138231893,
        5436003053874918619,
        6119766853874817756,
        18238141741817433176,
        15291547881600329180,
        16547936984919951199,
        8176918256333549158,
        12261070413986386661,
        5506737825174028137,
        7989182760411716713,
        17798064116822404580,
        11645801049091093097,
        16411497468756660201,
        7434222945297012083,
        3723439850461389687,
        11649272373429102199,
        1562699237605548669]


# Define the weather and time conditions that should be incorporated in the selected scenario
# Weather and time conditions (previously missing)
weather_time_conditions = ['morning', 'dry', 'clear']  


streetlight_ids = [      150,
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
        453,
        198,
        207,
        203,
        465,
        466]

npc_ids = ['npc1', 'npc2', 'npc3', 'npc4']

# Updated ddmin function from your first code
def ddmin(test: Callable, inp: Sequence, *test_args: Any) -> Sequence:
    """Reduce the input inp to the minimal set that still causes a test failure."""
    assert test(inp, *test_args) == PASS  # Ensure initial input triggers the failure (collision)

    # Initialize variables
    test_count = 0
    start_time = time.time()
    run = 0
    original_config = inp[:]
    original_config_idx = list(range(len(inp)))
    current_config_idx = original_config_idx[:]
    subsets = [current_config_idx]
    complement_offset = 0

    subset_width = max(40, len(str(inp)) // 2)

    print(f"Initial input: {inp}")
    print(f"{'Run':<5} | {'Granularity':<12} | {'Config Size':<12} | {'Subsets':<{subset_width}} | {'Test Step':<10} | {'Result'}")
    print("-" * (subset_width + 50))

    while len(current_config_idx) >= 2:
        run += 1
        config_size = len(current_config_idx)

        if len(subsets) < 2:
            subsets = zeller_split(subsets)

        subsets_str = str([list(map(lambda i: original_config[i], s)) for s in subsets])
        print(f"{run:<5} | {len(subsets):<12} | {config_size:<12} | {subsets_str:<{subset_width}}", end="")

        # Test subsets first
        for i, subset in enumerate(subsets):
            test_count += 1
            result = test(list(map(lambda x: original_config[x], subset)), *test_args)
            print(f" | {test_count:<10} | {'PASS' if result == PASS else 'FAIL'}")
            print(f"{'':<5} | {'':<12} | {'':<12} | Test subset: {list(map(lambda x: original_config[x], subset))}", end="")
            if result == PASS:  # If subset still causes collision
                subsets = [subset]
                current_config_idx = [c for s in subsets for c in s]
                print(f"\n{'':<5} | {'':<12} | {'':<12} | Reduced to: {list(map(lambda x: original_config[x], current_config_idx))}")
                break
        else:
            # Test complements if no subset fails
            for i in range(complement_offset, len(subsets)):
                complement = [c for s in subsets[:i] + subsets[i + 1:] for c in s]
                test_count += 1
                result = test(list(map(lambda x: original_config[x], complement)), *test_args)
                print(f" | {test_count:<10} | {'PASS' if result == PASS else 'FAIL'}")
                print(f"{'':<5} | {'':<12} | {'':<12} | Test complement: {list(map(lambda x: original_config[x], complement))}", end="")
                if result == PASS:  # If complement still causes collision
                    subsets = [complement]
                    current_config_idx = [c for s in subsets for c in s]
                    complement_offset = i + 1
                    print(f"\n{'':<5} | {'':<12} | {'':<12} | Reduced to: {list(map(lambda x: original_config[x], current_config_idx))}")
                    break
            else:
                if len(subsets) < len(current_config_idx):
                    subsets = zeller_split(subsets)
                    complement_offset = 0
                    print(f"\n{'':<5} | {'':<12} | {'':<12} | Increased granularity")
                else:
                    break  # No further reduction possible

        if len(subsets) == 1:
            current_config_idx = [c for s in subsets for c in s]
            subsets = [current_config_idx]

    total_time = time.time() - start_time
    minimal_input = list(map(lambda x: original_config[x], current_config_idx))
    print("-" * (subset_width + 50))
    print(f"Minimal failure-inducing input found: {minimal_input}")
    print(f"Total number of test steps: {test_count}")
    print(f"Total time to evaluate: {total_time:.6f} seconds")
    return minimal_input

def zeller_split(subsets, n=2):
    """Split the configuration into n subsets."""
    config = [c for s in subsets for c in s]
    length = len(config)
    n = min(length, len(subsets) * n)
    next_subsets = []
    start = 0
    for i in range(n):
        stop = start + (length - start) // (n - i)
        next_subsets.append(config[start:stop])
        start = stop
    return next_subsets


def test_function(inp):
    """Test if the input configuration causes a collision."""
    try:
        collision_result = get_collision_rate(inp)
        print(f"Collision result from get_collision_rate: {collision_result}")
        
        if collision_result == 1:
            print("Returning PASS (collision detected)")
            return PASS
        else:
            print("Returning FAIL (no collision detected)")
            return FAIL
    except Exception as e:
        print(f"Error during test: {e}")
        return FAIL


def get_collision_rate(inp):
    """Run simulation and get collision result from collision.py."""
    with open('test_input.json', 'w') as f:
        json.dump(inp, f)

    output_file = "collision_output.txt"
    if os.path.exists(output_file):
        os.remove(output_file)

    # Temporary files to store gnome-terminal PIDs
    carla_pid_file = "carla_terminal_pid.txt"
    remo_pid_file = "remo_terminal_pid.txt"
    replay_pid_file = "replay_terminal_pid.txt"
    collision_pid_file = "collision_terminal_pid.txt"

    try:
        # Step 1: Start CARLA and save terminal PID
        os.system(f"gnome-terminal -- bash -c 'cd carla_server; ./CarlaUE4.sh; exec bash' & echo $! > {carla_pid_file}")
        print("Started CARLA. Waiting 10 seconds...")
        time.sleep(10)

        # Step 2: Run bash script with Conda activation and save terminal PID
        os.system(f"gnome-terminal -- bash -c 'source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && bash run_remo.sh; exec bash' & echo $! > {remo_pid_file}")
        print("Started run_remo.sh. Waiting 5 seconds...")
        time.sleep(5)

        # Step 3: Run replay_json.py with dynamic NPC flags and save terminal PID
        npc_flags = [f"--{npc}" for npc in npc_ids if npc in inp]
        replay_command = f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && python3 replay_json.py {' '.join(npc_flags)}" if npc_flags else "source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && python3 replay_json.py"
        os.system(f"gnome-terminal -- bash -c '{replay_command}; exec bash' & echo $! > {replay_pid_file}")
        print("Started replay_json.py. Waiting 3 seconds...")
        time.sleep(3)

        # Step 4: Run collision.py in a terminal and redirect output, save terminal PID
        collision_command = f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && python3 collision.py > {output_file} 2>&1"
        os.system(f"gnome-terminal -- bash -c '{collision_command}' & echo $! > {collision_pid_file}")
        print("Started collision.py. Waiting 25 seconds...")
        time.sleep(25)  # Wait for 20s monitoring + buffer

        # Read the output
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                output = f.read()
            print(f"collision.py output:\n{output}")
        else:
            raise ValueError("collision_output.txt not created")

        # Parse "Collision" or "No Collision" from output
        collision_result = None
        if "Accident" in output:
            collision_result = 1
        elif "Safe" in output:
            collision_result = 0
        else:
            raise ValueError("Collision or No Collision not found in collision.py output")

        return collision_result

    except Exception as e:
        print(f"Error parsing collision result: {e}")
        return 0
    finally:
        # Always clean up terminals after each test
        print("Cleaning up terminals for this test step...")
        
        # Read and kill terminal PIDs
        for pid_file in [carla_pid_file, remo_pid_file, replay_pid_file, collision_pid_file]:
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    if pid:
                        os.system(f"kill -SIGTERM {pid}")
                        print(f"Terminated terminal with PID {pid} ({pid_file})")
                except Exception as e:
                    print(f"Error terminating terminal from {pid_file}: {e}")
                finally:
                    os.remove(pid_file)  # Clean up PID file

        # Additional cleanup for any lingering processes
        os.system("pkill -f CarlaUE4")
        os.system("pkill -f 'python3 replay_json.py'")
        os.system("pkill -f 'python3 collision.py'")
        
        if os.path.exists(output_file):
            os.remove(output_file)      
    
if __name__ == "__main__":
    initial_test_input =  building_ids + npc_ids + streetlight_ids + weather_time_conditions


    print(f"Initial Test Input: {initial_test_input}")
    minimal_input = ddmin(test_function, initial_test_input)
    print(f"Minimal failure-inducing input: {minimal_input}")


