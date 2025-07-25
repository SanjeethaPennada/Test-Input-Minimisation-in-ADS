import glob
import os
import sys
import time
import carla
import threading

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

class CollisionMonitor:
    def __init__(self, host='localhost', port=2000):
        # Connect to CARLA
        self.client = carla.Client(host, port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        
        # Variables for ego vehicle and sensor
        self.ego_vehicle = None
        self.collision_sensor = None
        self.collision_events = []
        
        # Ego vehicle type to monitor
        self.ego_vehicle_type = "vehicle.lincoln.mkz_2017"
    
    def setup_collision_sensor(self, ego_vehicle):
        """Attach a collision sensor to the ego vehicle."""
        blueprint_library = self.world.get_blueprint_library()
        collision_bp = blueprint_library.find('sensor.other.collision')
        self.collision_sensor = self.world.spawn_actor(collision_bp, carla.Transform(), attach_to=ego_vehicle)
        self.collision_sensor.listen(lambda event: self.on_collision())

    def on_collision(self):
        """Callback for collision events."""
        self.collision_events.append(1)  # Just track occurrence

    def monitor_ego_vehicle(self):
        """Monitor the world for the ego vehicle and attach a collision sensor."""
        while self.ego_vehicle is None:
            actors = self.world.get_actors()
            for actor in actors:
                if actor.type_id == self.ego_vehicle_type:
                    self.ego_vehicle = actor
                    self.setup_collision_sensor(self.ego_vehicle)
                    self.monitor_collisions()
                    return

    def monitor_collisions(self):
        """Monitor collisions for 10 seconds and log result."""
        time.sleep(10)  # Wait for collision events

        # Save result to file
        with open("collision_output.txt", "w") as file:
            file.write("Accident\n" if self.collision_events else "Safe\n")

        self.cleanup()

    def cleanup(self):
        """Clean up spawned actors."""
        if self.collision_sensor:
            self.collision_sensor.stop()
            self.collision_sensor.destroy()

def main():
    monitor = CollisionMonitor(host='localhost', port=2000)
    monitor.monitor_ego_vehicle()

if __name__ == '__main__':
    main()

