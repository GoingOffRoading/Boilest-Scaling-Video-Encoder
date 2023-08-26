import subprocess as sp
import shlex
import json

video = 'pythontest.mkv'

# Execute ffprobe and get the codec of the first video, audio, and subtitle stream
vcodec = sp.run(shlex.split(f'ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {video}'), capture_output=True).stdout
acodec = sp.run(shlex.split(f'ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {video}'), capture_output=True).stdout
scodec = sp.run(shlex.split(f'ffprobe -v error -select_streams s:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {video}'), capture_output=True).stdout

# Same as above, but outputs a larger object as json
# I abandoned this approach as it was too dificult to loop through the JSON to find the first stream of each codec type (vido, audio, subtitle)
# This would be ideal, as it reduces the file calls from three to one, so lets call this a someday task
#data = sp.run(shlex.split(f'ffprobe -loglevel error -show_streams -of json {video}'), capture_output=True).stdout
# Convert data from JSON string to dictionary
#d = json.loads(data)
# Uncoment these for diagnostics
# Get codecs
#video_codec = ({d["streams"][0]["codec_name"]})
#audio_codec = ({d["streams"][1]["codec_name"]})
#subtitle_format = ({d["streams"][2]["codec_name"]})

vc = vcodec.decode('utf-8')
ac = acodec.decode('utf-8')
sc = scodec.decode('utf-8')

if vc == 'av1':
    print ('done')
else if 
    
    
else:
    print ('not AV1')