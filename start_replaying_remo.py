#!/usr/bin/env python

import glob
import os
import sys
import time

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
    argparser.add_argument('-d', '--duration', metavar='D', default=5.0, type=float, help='duration (default: 5.0)')
    argparser.add_argument('-f', '--recorder-filename', metavar='F', default="test.log", help='recorder filename (test.log)')
    argparser.add_argument('-c', '--camera', metavar='C', default=0, type=int, help='camera follows an actor (ex: 82)')
    argparser.add_argument('-x', '--time-factor', metavar='X', default=1.0, type=float, help='time factor (default 1.0)')
    argparser.add_argument('-i', '--ignore-hero', action='store_true', help='ignore hero vehicles')
    argparser.add_argument('--move-spectator', action='store_true', help='move spectator camera')
    argparser.add_argument('--spawn-sensors', action='store_true', help='spawn sensors in the replayed world')
    args = argparser.parse_args()

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        # Set the time factor for the replayer
        client.set_replayer_time_factor(args.time_factor)

        # Set to ignore the hero vehicles or not
        client.set_replayer_ignore_hero(args.ignore_hero)

        # Set to ignore the spectator camera or not
        client.set_replayer_ignore_spectator(not args.move_spectator)

        # Get the current working directory
        cwd = os.getcwd()

        # Join current working directory with the filename
        filename = os.path.join(cwd, args.recorder_filename)

        # Replay the session
        print(client.replay_file(filename, args.start, args.duration, args.camera, args.spawn_sensors))



        # Get all actors in the world
        world = client.get_world()


    finally:
        pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')

