import subprocess

def ffencoder(FILEPATH):
    command = subprocess.Popen(
        ['ffmpeg',
        '-i', FILEPATH,
        '-vcodec', 'libsvtav1',
        '-crf', '20',
        '-preset', '5',
        '-g', '240',
        '-pix_fmt', 'yuv420p10le',
        '-c:s', 'srt',
        '-c:a', 'libopus',
        'pythontest.mkv'],
        stderr=subprocess.PIPE,
        text=True)

    print(command.stderr.read())




import json

json_stuff = '{"file_path": "/boil_watch/newtest.mkv", "encode_string": "-c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le-c:s srt", "file": "newtest.mkv"}'
d = json.loads(json_stuff)

input_file = (d["file_path"])
print (input_file)

ffmpeg_string = (d["encode_string"])
print (ffmpeg_string)



ffmpeg_string = input_file + ' ' + ffmpeg_string
print (ffmpeg_string)
