import carla

# Connect to the CARLA server
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
world = client.get_world()

# Get the current weather
weather = world.get_weather()

# Print all relevant weather parameters
print("Current Weather Parameters:")
print(f"Sun Azimuth Angle: {weather.sun_azimuth_angle}")
print(f"Sun Altitude Angle: {weather.sun_altitude_angle}")
print(f"Precipitation: {weather.precipitation}")
print(f"Precipitation Deposits: {weather.precipitation_deposits}")
print(f"Wind Intensity: {weather.wind_intensity}")
print(f"Fog Density: {weather.fog_density}")
print(f"Fog Distance: {weather.fog_distance}")
print(f"Fog Falloff: {weather.fog_falloff}")

