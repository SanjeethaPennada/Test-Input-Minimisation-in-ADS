#!/usr/bin/env python

import glob
import os
import sys
import time
import json

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import argparse


def main():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument('--host', metavar='H', default='127.0.0.1', help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument('-p', '--port', metavar='P', default=2000, type=int, help='TCP port to listen to (default: 2000)')
    argparser.add_argument('-s', '--start', metavar='S', default=0.0, type=float, help='starting time (default: 0.0)')
    argparser.add_argument('-d', '--duration', metavar='D', default=5, type=float, help='duration (default: 5)')
    argparser.add_argument('-f', '--recorder-filename', metavar='F', default="test.log", help='recorder filename (test.log)')
    argparser.add_argument('-c', '--camera', metavar='C', default=0, type=int, help='camera follows an actor (ex: 82)')
    argparser.add_argument('-x', '--time-factor', metavar='X', default=1.0, type=float, help='time factor (default 1.0)')
    argparser.add_argument('-i', '--ignore-hero', action='store_true', help='ignore hero vehicles')
    argparser.add_argument('--move-spectator', action='store_true', help='move spectator camera')
    argparser.add_argument('--spawn-sensors', action='store_true', help='spawn sensors in the replayed world')
    argparser.add_argument('--output-json', metavar='O', default='test.json', help='output JSON filename (test.json)')
    args = argparser.parse_args()

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(10.0)

        # Set the time factor for the replayer
        client.set_replayer_time_factor(args.time_factor)

    
        # Get the current working directory
        cwd = os.getcwd()

        # Join current working directory with the filename
        filename = os.path.join(cwd, args.recorder_filename)
        # Replay the session
        print(client.replay_file(filename, args.start, args.duration, args.camera, args.spawn_sensors)) 

        # Initialize data collection
        data = {
            'frames': []
        }

        # Record the state throughout the duration of the replay
        start_time = time.time()
        print(start_time) #this start_time - the start_time in first frame gives time.sleep in npc.py
        while time.time() - start_time < args.duration:
            # Wait a moment for the world to populate
          
         
         
            # Poll for current state
            frame_data = {
                'timestamp': [(time.time() - start_time)],
                'start_time': [start_time],
                'time.time': [time.time()],
                'vehicles': []
            }

            # Gather current actor states
            actors = client.get_world().get_actors()
            for actor in actors:
                # Collect vehicle information
                if 'vehicle.' in actor.type_id:
                    transform = actor.get_transform()
                    vehicle_info = {
                        'id': actor.id,
                        'type': actor.type_id,
                        'location': {
                            'x': transform.location.x,
                            'y': transform.location.y,
                            'z': transform.location.z,
                        },
                        'rotation': {
                            'pitch': transform.rotation.pitch,
                            'yaw': transform.rotation.yaw,
                            'roll': transform.rotation.roll,
                        },
                        'velocity': {
                            'x': actor.get_velocity().x,
                            'y': actor.get_velocity().y,
                            'z': actor.get_velocity().z,
                        },
                        'angular_velocity': {
                            'x': actor.get_angular_velocity().x,
                            'y': actor.get_angular_velocity().y,
                            'z': actor.get_angular_velocity().z,
                        },
                    }
                    frame_data['vehicles'].append(vehicle_info)

               

            # Append frame data to the overall data structure
            data['frames'].append(frame_data)

        # Save collected data to JSON file
        with open(args.output_json, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        print(f'Data saved to {args.output_json}')

    finally:
        pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')
        
        


