import json

total_analysis = []

with open("output.json", "w") as fp:
    json.dump(total_analysis, fp)