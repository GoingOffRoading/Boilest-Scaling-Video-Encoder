ffprobe -v quiet -print_format json -show_format -show_streams test.mkv




import subprocess as sp
import shlex
import json

video = 'test.mkv'

# Execute ffprobe (to show streams), and get the output in JSON format
data = sp.run(shlex.split(f'ffprobe -loglevel error -show_streams -of json {video}'), capture_output=True).stdout

# Convert data from JSON string to dictionary
d = json.loads(data)

#print(d['codec_name'])
print(json.dumps(d, indent = 4, sort_keys=True))
