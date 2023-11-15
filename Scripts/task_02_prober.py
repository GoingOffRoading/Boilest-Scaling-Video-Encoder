from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib





def ffprobe(ffinder_json):
    # This function is kicked off from the individual file results from the ffinder function, and then do three functions:
    # 1) For each file, run ffprobe to get details on the file
    # 2) Loop through those the ffprobe results to determine if any changes need to be made to the video container or it's video, audio, or subtitle streams 
    # 3) Determine if the file needs to be encoded, and if yes, pass the changes to the fencoder function


    # Using subprocess to call FFprobe, get JSON back on the video's container, and streams, then display the outputs  
    file_path = (ffinder_json["file_path"])
    file_name = (ffinder_json["file_name"])
    file_full_path = os.path.join(file_path,file_name)    
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout', '-of', 'json', file_full_path]
    print ("ffprobe's command on " + file_name + ":")
    print (cmnd)
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)
    print ("ffprobe's results on " + file_name + ":")
    print(json.dumps(d, indent=3, sort_keys=True))
     
    # Now that we have FFProbe's output, we want to evaluate the container, video stream, audio stream, and subtitle formats
    # If those values don't match the input templte, then we flip encode_decision to yes, and transmit the results to fencoder

    # Setting starter variables.  These are revisited throughout the loop.
    encode_string = str()
    encode_decision = 'no'
    original_string = str()
    
    # Determine if the container needs to be changed
    original_container = (d['format']['format_name'])
    print ('Original Video container is: ' + original_container)
    if original_container != 'matroska,webm' or pathlib.Path(ffinder_json["file_name"]).suffix != '.mkv':
        file_name = (ffinder_json["file_name"])
        file_name = Path(file_name).stem 
        ffmpeg_output_file = file_name + '.mkv'
        encode_decision = 'yes'
        print ('Container is not MKV, converting container')
    else:
        ffmpeg_output_file = file_name
        print (file_name + ' is already .mkv, no need to change container')
    
    # Stream Loop: We need to loop through each of the streams, and make decisions based on the codec in the stream
    streams_count = d['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    for i in range (0,streams_count):
        if d['streams'][i]['codec_type'] == 'video':
            codec_name = d['streams'][i]['codec_name'] 
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (ffinder_json["ffmpeg_video_codec"]):
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != (ffinder_json["ffmpeg_video_codec"]):
                encode_decision = 'yes'
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_video_string"])
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the video codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        elif d['streams'][i]['codec_type'] == 'audio':
            codec_name = d['streams'][i]['codec_name'] 
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (ffinder_json["ffmpeg_audio_codec"]):
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:a copy'
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
                # No need to change encode_decision as the audio codec is in the desired format
            elif codec_name != 'opus' and d['streams'][i]['channel_layout'] == '5.1(side)':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus -af aformat=channel_layouts="7.1|5.1|stereo"'
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ' and, using ' + d['streams'][i]['channel_layout'] +', filtering, then encoding stream')
                # encode_decision = yes as the audio codec is not in the desired format... libopus has problems with 5.1(side) channel layout in ffmpeg so we catch it here.  Unclear if we can combine this step with the next one
            elif codec_name != (ffinder_json["ffmpeg_audio_codec"]):
                #encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus' 
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_audio_string"])
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the audio codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        elif d['streams'][i]['codec_type'] == 'subtitle':
            codec_name = d['streams'][i]['codec_name'] 
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (ffinder_json["ffmpeg_subtitle_format"]):
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy'
                # No need to change encode_decision as the subtitles are in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
            elif d['streams'][i]['codec_name'] == 'hdmv_pgs_subtitle':
                # These are image based subtitles, and can't be converted to text type
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy' 
                # No need to change encode_decision as we can't change picture subtitles into text subtitles
                print ('Stream ' + str(i) + ' is ' + codec_name + ': a pain in the dick, and nothing we can do but copy the stream')
            elif codec_name != (ffinder_json["ffmpeg_subtitle_format"]):
                #encode_string = encode_string + ' -map 0:' + str(i) + ' -scodec subrip' 
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_subtitle_string"]) 
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
            else:
                print ('Something is broken with stream ' + str(i))

        # No idea if attachments provide any value.  Sr far: no
        elif d['streams'][i]['codec_type'] == 'attachment':
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type']
            print ('Stream is attachment, ignore')
            # Progably not a great idea to ditch these, but whatever.  So far in discovery, the attachments have been font files.         
        else:
            print ('fuck')
            
    print ('encode_string is: ' + encode_string)
    print ('encode_decision is: ' + encode_decision)
    print ('original_string is: ' + original_string)
       
    # Part 2 determines if the string is needed
    if encode_decision == 'no': 
        print (file_name + ' does not need encoding')
    else:
        print (file_name + ' needs encoding')
        fprober_json = {'ffmpeg_encoding_string':encode_string, 'ffmpeg_output_file':ffmpeg_output_file, 'original_string':original_string}
        fprober_json.update(ffinder_json) 
        return(fprober_json)
        print(json.dumps(fprober_json, indent=3, sort_keys=True))

