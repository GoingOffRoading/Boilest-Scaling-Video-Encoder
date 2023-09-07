import json
from pathlib import Path
import os

def ffmpeger(ffmpeg_json):
    
    print ('================= ffmpeger JSON inputs =================')
    print(json.dumps(ffmpeg_json, indent=3, sort_keys=True))
    
    # ffmpeg is ffmpeg + settings + input file + encoding settings + output file
    # So we're going to grab each of those pieces

    # Need to get the ffmpeg settings
    ffmpeg_settings = (ffmpeg_json["ffmpeg_settings"])
    #print ('ffmpeg settings are: ' + ffmpeg_settings)
        
    # Need to get the input filepath
    file_path = (ffmpeg_json["file_path"])
    file_name = (ffmpeg_json["file_name"])
    ffmeg_input_file = os.path.join(file_path,file_name)
    #print ('input file is: ' + ffmeg_input_file)
    
    # Need to get the encoding settings     
    ffmpeg_encoding_settings = (ffmpeg_json["ffmpeg_encoding_string"])
    #print ('encoding settings are: ' + ffmpeg_encoding_settings)
    
    # Need to get the output filepath   
    file_name = Path(file_name).stem
    output_extension = (ffmpeg_json["ffmeg_container_extension"])
    #print ('filename is currently: ' + file_name)
    ffmpeg_output_file = '/boil_hold/' + file_name + '.' + output_extension
    #print ('file name with path is: ' + ffmpeg_output_file)
    
    # All together now
    print ('=============== assembled ffmpeg command ===============')
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + ffmeg_input_file + '"' + ffmpeg_encoding_settings + ' ".' + ffmpeg_output_file + '"'
    print (ffmpeg_command)    
    print ('=============== executing ffmpeg =======================')

    #print (ffmpeg_command)
    print ('Please hold')
    os.system(ffmpeg_command)
    
    # Would love to revisit this as a subprocess, but was having issues getting everything to slice as desired
    #print ('=============== assembled ffmpeg command ===============')
    #ffmpeg_settings = ffmpeg_settings.split()
    #ffmpeg_settings = ', '.join(ffmpeg_settings)
    #ffmpeg_encoding_settings = ffmpeg_encoding_settings.split()
    #ffmeg_input_file = '"' + ffmeg_input_file + '"'
    #ffmpeg_output_file = '"' + ffmpeg_output_file + '"'
    #ffmpeg_command = 'ffmpeg', ffmpeg_settings, '-i', ffmeg_input_file, ffmpeg_encoding_settings,ffmpeg_output_file
    #print (ffmpeg_command)    
    #print ('=============== executing ffmpeg =======================')
    
    #p = subprocess.run(cmnd, capture_output=True).stdout
    #d = json.loads(p)

    print ('=============== Checking output =======================')
    
    if os.path.exists(ffmeg_input_file and ffmpeg_output_file):
        print( ffmeg_input_file + ' and ' + ffmpeg_output_file + ' Files Exists')
        input_file_stats = os.stat(ffmeg_input_file)
        print(f'Original file Size in MegaBytes is {input_file_stats.st_size / (1024 * 1024)}') 
        output_file_stats = os.stat(ffmpeg_output_file)
        print(f'Encoded file Size in MegaBytes is {output_file_stats.st_size / (1024 * 1024)}') 
        print('Removing ' + ffmeg_input_file)
        #os.remove(ffmeg_input_file) 
        print('Moving ' + ffmpeg_output_file + ' to ' + ffmeg_input_file)
        #os.rename(ffmpeg_output_file, ffmeg_input_file)
        print ('Done')    
    else:
         print("Something Broke")
    
    
    