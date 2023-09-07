import  json, subprocess, os
def fprober(ffinder_json):
    
    # Uncomment to see the incoming JSON
    #print(json.dumps(filename, indent=3, sort_keys=True))
    
    # Need to assemble the full filepath to pass to FFprobe
    file_path = (filename["file_path"])
    file_name = (filename["file_name"])
    ffprobe_path = os.path.join(file_path,file_name)
    
    print ('Going to execute FFprobe on: ' + ffprobe_path)
    
    # Using subprocess to call FFprobe, get JSON back    
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name', '-of', 'json', ffprobe_path]
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)

    # Uncomment this if you want to do diagnostics on the JSON FFmpeg outputs
    #print(json.dumps(d, indent=3, sort_keys=True))
    
    
    # Get the container type from the FFProbe output
    original_container = (d["format"]["format_name"])
    #print (original_container)
    
    # Get the video codec from the first video stream
    for stream in d['streams']:
        if stream['codec_type']=="video":
            original_video_codec = stream['codec_name']
            break
    #print(original_audio_codec)
    
     # Get the video codec from the first audio stream
    for stream in d['streams']:
        if stream['codec_type']=="audio":
            original_audio_codec = stream['codec_name']
            break
    #print(original_audio_codec)

    # Get the subtitle format from the first subtitle stream
    for stream in d['streams']:
        if stream['codec_type']=="subtitle":
            ffmpeg_subtitle_format = stream['codec_name']
            break
    #print(original_audio_codec)
    
    # Here we check the output of ffprobe against the configurations for the library
    # See the template.json
    
    # Part 1 (bellow) checks the container, codecs, formats and builds the relevant ffmpeg string 
    
    # Create an empty string variable that will become our FFmpeg variables
    encode = str()

    # Determine if the container needs to be changed
    if original_container != (filename["ffmpeg_container"]):
        print (ffprobe_path + ' is using ' + original_container + ', not' + (filename["ffmpeg_container"]))

    # Determine if the video needs to be re-encoded
    if original_video_codec != (filename["ffmpeg_video_codec"]):
        print (ffprobe_path + ' is using ' + original_video_codec + ', not' + (filename["ffmpeg_video_codec"]))
        encode = encode + (filename["ffmpeg_video_string"])
    
    # Determine if the audio needs to be re-encoded
    if original_audio_codec != (filename["ffmpeg_audio_codec"]):
        print (ffprobe_path + ' is using ' + original_audio_codec + ', not ' + (filename["ffmpeg_audio_codec"]))
        encode = encode + (filename["ffmpeg_audio_string"])
        
    # Determine if the subtitles needs to be re-formatted
    if ffmpeg_subtitle_format != (filename["ffmpeg_subtitle_format"]):
        print (ffprobe_path + ' is using ' + original_subtitle_codec + ', not ' + (filename["ffmpeg_subtitle_format"]))
        encode = encode + (filename["ffmpeg_subtitle_string"])  
    
    # Part 2 determines if the string is needed
    if original_container == (filename["ffmpeg_container"]) and original_video_codec == (filename["ffmpeg_video_codec"]) and original_audio_codec == (filename["ffmpeg_audio_codec"]) and (filename["ffmpeg_subtitle_format"]): 
        print (ffprobe_path + ' is using all of the correct containers and codecs')
    else:
        print (ffprobe_path + ' is going to have to be processed by FFmpeg')
        ffmpeg_json = {'ffmpeg_encoding_string':encode}
        fprober_json.update(ffmpeg_json)
        fprober_json.update(filename) 
        print(json.dumps(fprober_json, indent=3, sort_keys=True))
        return fprober_json
        
        
        
    
    
    
    
