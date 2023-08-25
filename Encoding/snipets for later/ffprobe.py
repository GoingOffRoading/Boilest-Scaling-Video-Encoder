ffprobe -v quiet -print_format json -show_format -show_streams test.mkv


 ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of json test.mkv




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








import subprocess as sp
import shlex
import json

video = 'pythontest.mkv'

# Execute ffprobe (to show streams), and get the output in JSON format
data = sp.run(shlex.split(f'ffprobe -loglevel error -show_streams -of json {video}'), capture_output=True).stdout

# Convert data from JSON string to dictionary
d = json.loads(data)

# Uncoment these for diagnostics
#print(d['codec_name'])
#print(json.dumps(d, indent = 4, sort_keys=True))

# Get codecs
#print({d["streams"][0]["codec_name"]})
#print({d["streams"][0]["pix_fmt"]})
#print({d["streams"][1]["codec_name"]})
#print({d["streams"][2]["codec_name"]})

video_codec = ({d["streams"][0]["codec_name"]})
video_format =({d["streams"][0]["pix_fmt"]})
audio_codec = ({d["streams"][1]["codec_name"]})
subtitle_format = ({d["streams"][2]["codec_name"]})

if (video_codec) == {'av1'} and video_format == {'yuv420p10le'} and audio_codec == {'opus'} and subtitle_format == {'subrip'}:
    print ('all done')
else:
    print ('f')
    
    print(json.dumps(d, indent = 4, sort_keys=True))
