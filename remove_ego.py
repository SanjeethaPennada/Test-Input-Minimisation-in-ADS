import json

# Load test.json
with open("test.json", "r") as file:
    scenario_data = json.load(file)

# Identify and remove ego vehicle from each frame
for frame in scenario_data["frames"]:
    frame["vehicles"] = [v for v in frame["vehicles"] if v.get("id")!=698]

# Save as NPC.json
with open("NPC.json", "w") as file:
    json.dump(scenario_data, file, indent=4)

print("NPC.json created successfully without ego vehicle.")
