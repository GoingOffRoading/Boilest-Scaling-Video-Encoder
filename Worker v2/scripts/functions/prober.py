import  json, subprocess
def probe_file(filename):
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name', '-of', 'json', filename]
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)
    print(json.dumps(d, indent=3, sort_keys=True))
    video_codec = (d["streams"][0]["codec_name"])
    print (video_codec)
    
    for stream in d['streams']:
        if stream['codec_type']=="audio":
            cname = stream['codec_name']
            break
    print(cname)
