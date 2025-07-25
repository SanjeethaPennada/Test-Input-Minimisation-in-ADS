import glob
import os
import sys
import time
import carla
import math
from collections import deque
import numpy as np

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# KING collision clusters (updated to match the figure)
KING_CLUSTERS = {
    'a': 'Merge',
    'b': 'Behind',
    'c': 'Cut-off',
    'd': 'Side',
    'e': 'Head-on',
    'f': 'T-bone',
    'g': 'Front'
}

class TrajectoryTracker:
    def __init__(self, max_history_seconds=2.0, update_interval=0.1):
        self.max_history_seconds = max_history_seconds
        self.update_interval = update_interval
        self.ego_trajectory = deque(maxlen=int(max_history_seconds / update_interval))
        self.adversarial_trajectory = deque(maxlen=int(max_history_seconds / update_interval))

    def update_trajectories(self, ego_vehicle, adversarial_vehicle):
        current_time = time.time()
        ego_pos = ego_vehicle.get_location()
        ego_yaw = math.radians(ego_vehicle.get_transform().rotation.yaw)
        self.ego_trajectory.append((current_time, ego_pos.x, ego_pos.y, ego_yaw))

        if adversarial_vehicle:
            adv_pos = adversarial_vehicle.get_location()
            adv_yaw = math.radians(adversarial_vehicle.get_transform().rotation.yaw)
            self.adversarial_trajectory.append((current_time, adv_pos.x, adv_pos.y, adv_yaw))

    def _get_closest_data(self, trajectory, target_time):
        closest_data = None
        min_diff = float('inf')
        for data in trajectory:
            time_diff = abs(data[0] - target_time)
            if time_diff < min_diff:
                min_diff = time_diff
                closest_data = data
        return closest_data, min_diff

    def check_direction(self, collision_time):
        ego_data, ego_diff = self._get_closest_data(self.ego_trajectory, collision_time)
        adv_data, adv_diff = self._get_closest_data(self.adversarial_trajectory, collision_time)

        if ego_data is None or adv_data is None or ego_diff > 0.05 or adv_diff > 0.05:
            return "insufficient_data"

        yaw_diff = abs(math.degrees((ego_data[3] - adv_data[3]) % (2 * math.pi)))
        yaw_diff = min(yaw_diff, 360 - yaw_diff)

        if 80 <= yaw_diff <= 110:
            return "t_bone"
        elif 135 <= yaw_diff <= 225:
            return "opposite_direction"
        elif yaw_diff < 45:
            return "same_direction"
        else:
            return "other"

    def check_relative_position(self, collision_time):
        ego_data, ego_diff = self._get_closest_data(self.ego_trajectory, collision_time)
        adv_data, adv_diff = self._get_closest_data(self.adversarial_trajectory, collision_time)

        if ego_data is None or adv_data is None or ego_diff > 0.05 or adv_diff > 0.05:
            return "insufficient_data"

        ego_x, ego_y, ego_yaw = ego_data[1], ego_data[2], ego_data[3]
        adv_x, adv_y = adv_data[1], adv_data[2]

        rel_x = adv_x - ego_x
        rel_y = adv_y - ego_y
        cos_yaw = math.cos(ego_yaw)
        sin_yaw = math.sin(ego_yaw)
        local_x = rel_x * cos_yaw + rel_y * sin_yaw

        return "rear" if local_x < 0 else "front"

    def check_center_angle(self, collision_time):
        ego_data, ego_diff = self._get_closest_data(self.ego_trajectory, collision_time)
        adv_data, adv_diff = self._get_closest_data(self.adversarial_trajectory, collision_time)

        if ego_data is None or adv_data is None or ego_diff > 0.05 or adv_diff > 0.05:
            return None

        delta_x = adv_data[1] - ego_data[1]
        delta_y = adv_data[2] - ego_data[2]
        angle_deg = math.degrees(math.atan2(delta_y, delta_x)) % 360
        return angle_deg

class CollisionMonitor:
    def __init__(self, host='localhost', port=2000):
        self.client = carla.Client(host, port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        self.ego_vehicle = None
        self.collision_sensor = None
        self.collision_events = []
        self.trajectory_tracker = TrajectoryTracker()
        self.ego_vehicle_type = "vehicle.lincoln.mkz_2017"

    def setup_collision_sensor(self, ego_vehicle):
        blueprint_library = self.world.get_blueprint_library()
        collision_bp = blueprint_library.find('sensor.other.collision')
        self.collision_sensor = self.world.spawn_actor(collision_bp, carla.Transform(), attach_to=ego_vehicle)
        self.collision_sensor.listen(lambda event: self.on_collision(event))

    def on_collision(self, event):
        if self.collision_events:
            return

        collision_time = time.time()
        other_actor = event.other_actor
        self.trajectory_tracker.update_trajectories(self.ego_vehicle, other_actor)

        impulse = event.normal_impulse
        angle = math.atan2(impulse.y, impulse.x) * 180 / math.pi
        if -45 <= angle <= 45:
            impact_direction = 'rear'
        elif 135 <= angle or angle <= -135:
            impact_direction = 'front'
        else:
            impact_direction = 'side'

        direction = self.trajectory_tracker.check_direction(collision_time)
        position = self.trajectory_tracker.check_relative_position(collision_time)
        center_angle = self.trajectory_tracker.check_center_angle(collision_time)

        ego_yaw = self.ego_vehicle.get_transform().rotation.yaw
        other_yaw = other_actor.get_transform().rotation.yaw
        yaw_diff = abs((ego_yaw - other_yaw) % 360)
        yaw_diff = min(yaw_diff, 360 - yaw_diff)
        fallback_direction = (
	    't_bone' if 80 <= yaw_diff <= 110
	    else 'same_direction' if yaw_diff < 45
	    else 'opposite_direction' if 135 <= yaw_diff <= 225
	    else 'other')

        relative_movement = direction if direction != "insufficient_data" else fallback_direction
        effective_position = position if position != "insufficient_data" else impact_direction

        self.collision_events.append({
            'relative_movement': relative_movement,
            'relative_position': effective_position,
            'center_angle': center_angle
        })

    def classify_collision(self, info):
        move = info['relative_movement']
        pos = info['relative_position']
        angle = info['center_angle']
        if angle is None:
            return None

        if move == 't_bone':
            return 'f'  # T-bone
        elif move == 'same_direction':
            if pos == 'front':
                return 'c'  # Cut-off
            elif pos == 'rear':
                return 'b' if 170 <= angle <= 190 else 'a'  # Behind or Merge
        elif move == 'opposite_direction':
            return 'e' if 320 <= angle <= 360 or 170 <= angle <= 190 else 'g'  # Head-on or Front
        elif move == 'other':
            return 'g' #Front
        return None


    def monitor_ego_vehicle(self):
        for _ in range(10):
            actors = self.world.get_actors()
            for actor in actors:
                if actor.type_id == self.ego_vehicle_type:
                    self.ego_vehicle = actor
                    self.setup_collision_sensor(actor)
                    self.monitor_collisions()
                    return
            time.sleep(1)

        with open("collision_output.txt", "w") as f:
            f.write("Safe\n")

    def monitor_collisions(self):
        start = time.time()
        while time.time() - start < 10:
            if self.ego_vehicle:
                self.trajectory_tracker.update_trajectories(self.ego_vehicle, None)
            time.sleep(0.1)

        with open("collision_output.txt", "w") as f:
            if self.collision_events:
                info = self.collision_events[0]
                cluster = self.classify_collision(info)
                print("\n--- Collision Classification Debug Info ---")
                print(f"Relative Movement: {info['relative_movement']} (t_bone, same_direction, opposite_direction, other)")
                print(f"Relative Position: {info['relative_position']} (front, rear, side)")
                print(f"Center Angle between vehicles: {info['center_angle']}°")
                print(f"-> Classification Cluster: {cluster} ({KING_CLUSTERS.get(cluster, 'Unknown')})")
                print("------------------------------------------------\n")


                f.write(f"Accident: {KING_CLUSTERS.get(cluster, 'Unclassified')}\n" if cluster else "Unclassified\n")
            else:
                f.write("Safe\n")

        self.cleanup()

    def cleanup(self):
        if self.collision_sensor:
            self.collision_sensor.stop()
            self.collision_sensor.destroy()
        self.ego_vehicle = None
        self.collision_events.clear()


def main():
    monitor = CollisionMonitor()
    monitor.monitor_ego_vehicle()


if __name__ == '__main__':
    main()

