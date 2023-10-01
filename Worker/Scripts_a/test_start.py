from tasks import ffinder
import json

json_file = f'/Scripts/Templates/AV1_test.json'
f = open(json_file)
json_template = json.load(f)
ffinder(json_template)