#!/usr/bin/env python
#This is used to replay NPCs i.e., NPCs travel pre defined route and this code is used to replay their path. 

import glob
import os
import sys
import time
import json
import argparse
import threading

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

def spawn_vehicles_from_json(world, json_data, allowed_vehicle_ids=None, start_time=None):
    vehicles = {}
    ego_vehicle = None

    if not allowed_vehicle_ids:
        print("No vehicles will be spawned as no specific NPCs were specified.")
        return vehicles, ego_vehicle

    for frame_idx, frame in enumerate(json_data['frames']):
        current_timestamp = frame['timestamp'][0]

        if start_time is not None:
            target_sim_time = start_time + current_timestamp
            current_sim_time = world.get_snapshot().timestamp.elapsed_seconds
            sleep_duration = target_sim_time - current_sim_time
            if sleep_duration > 0:
                time.sleep(sleep_duration)
        elif frame_idx > 0:
            previous_timestamp = json_data['frames'][frame_idx - 1]['timestamp'][0]
            sleep_duration = current_timestamp - previous_timestamp
            if sleep_duration > 0:
                time.sleep(sleep_duration)

        data = [v for v in frame['vehicles'] if v['id'] in allowed_vehicle_ids]
        for vehicle_data in data:
            vehicle_id = vehicle_data['id']
            vehicle_type = vehicle_data['type']
            position = carla.Location(**vehicle_data['location'])
            rotation = carla.Rotation(**vehicle_data['rotation'])
            transform = carla.Transform(position, rotation)

            if vehicle_id not in vehicles:
                blueprint = world.get_blueprint_library().find(vehicle_type)
                if not blueprint:
                    print(f"Warning: Blueprint for {vehicle_type} not found.")
                    continue

                vehicle = world.try_spawn_actor(blueprint, transform)
                if vehicle:
                    vehicles[vehicle_id] = vehicle
                    print(f"Spawned vehicle {vehicle_id} ({vehicle_type})")
                    if ego_vehicle is None:
                        ego_vehicle = vehicle
                else:
                    print(f"Failed to spawn vehicle {vehicle_id}")
            else:
                vehicles[vehicle_id].set_transform(transform)

    return vehicles, ego_vehicle

def monitor_ego_vehicle_spawn(world, ego_type="vehicle.lincoln.mkz_2017", callback=None):
    print(f"Monitoring for ego vehicle of type {ego_type}...")
    vehicle = None
    while True:
        snapshot = world.get_snapshot()
        # Filter actors using world.get_actors().filter
        actors = world.get_actors().filter(ego_type)
        for actor in actors:
            if not vehicle:
                vehicle = actor
                spawn_time = snapshot.timestamp.elapsed_seconds
                print(f"Ego vehicle {ego_type} (ID: {actor.id}) detected at sim time {spawn_time}. Starting replay.")
                if callback:
                    callback(spawn_time)
                return

def get_vehicle_ids_from_json(json_data):
    if not json_data['frames']:
        return []
    first_frame = json_data['frames'][0]
    return [vehicle['id'] for vehicle in first_frame['vehicles']]

def main():
    parser = argparse.ArgumentParser(description="Replay vehicles from NPC.json based on specified IDs.")
    parser.add_argument('--npc1', action='store_true', help='Replay the first vehicle')
    parser.add_argument('--npc2', action='store_true', help='Replay the second vehicle')
    parser.add_argument('--npc3', action='store_true', help='Replay the third vehicle')
    parser.add_argument('--npc4', action='store_true', help='Replay the fourth vehicle')
    parser.add_argument('--npc5', action='store_true', help='Replay the fifth vehicle')
    parser.add_argument('--npc6', action='store_true', help='Replay the sixth vehicle')
    parser.add_argument('--npc7', action='store_true', help='Replay the seventh vehicle')
    parser.add_argument('--npc8', action='store_true', help='Replay the eighth vehicle')
    parser.add_argument('--npc9', action='store_true', help='Replay the ninth vehicle')
    parser.add_argument('--npc10', action='store_true', help='Replay the tenth vehicle')
    args = parser.parse_args()

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    json_file_path = 'NPC.json'
    with open(json_file_path) as f:
        scenario_data = json.load(f)

    all_vehicle_ids = get_vehicle_ids_from_json(scenario_data)
    print(f"All vehicle IDs in NPC.json: {all_vehicle_ids}")

    allowed_vehicle_ids = set()
    if args.npc1 and len(all_vehicle_ids) >= 1:
        allowed_vehicle_ids.add(all_vehicle_ids[0])
    if args.npc2 and len(all_vehicle_ids) >= 2:
        allowed_vehicle_ids.add(all_vehicle_ids[1])
    if args.npc3 and len(all_vehicle_ids) >= 3:
        allowed_vehicle_ids.add(all_vehicle_ids[2])
    if args.npc4 and len(all_vehicle_ids) >= 4:
        allowed_vehicle_ids.add(all_vehicle_ids[3])
    if args.npc5 and len(all_vehicle_ids) >= 5:
        allowed_vehicle_ids.add(all_vehicle_ids[4])
    if args.npc6 and len(all_vehicle_ids) >= 6:
        allowed_vehicle_ids.add(all_vehicle_ids[5])
    if args.npc7 and len(all_vehicle_ids) >= 7:
        allowed_vehicle_ids.add(all_vehicle_ids[6])
    if args.npc8 and len(all_vehicle_ids) >= 8:
        allowed_vehicle_ids.add(all_vehicle_ids[7])
    if args.npc9 and len(all_vehicle_ids) >= 9:
        allowed_vehicle_ids.add(all_vehicle_ids[8])
    if args.npc10 and len(all_vehicle_ids) >= 10:
        allowed_vehicle_ids.add(all_vehicle_ids[9])

    if not allowed_vehicle_ids:
        print("No NPC arguments provided. No vehicles will be spawned.")
    else:
        print(f"Replaying only vehicles with IDs: {allowed_vehicle_ids}")

    def start_replay(spawn_time):
        vehicles, replay_ego_vehicle = spawn_vehicles_from_json(world, scenario_data, allowed_vehicle_ids, spawn_time)
        try:
            print("Replay complete. Keeping simulation alive.")
            while True:
                world.tick()
        except KeyboardInterrupt:
            print("Ending the simulation.")
        finally:
            for vehicle in vehicles.values():
                vehicle.destroy()
            print("Vehicles cleaned up.")

    monitor_thread = threading.Thread(target=monitor_ego_vehicle_spawn, args=(world, "vehicle.lincoln.mkz_2017", start_replay), daemon=True)
    monitor_thread.start()

    try:
        monitor_thread.join()
        while True:
            world.tick()
    except KeyboardInterrupt:
        print("Program interrupted. Exiting.")
        sys.exit(0)

if __name__ == '__main__':
    main()
