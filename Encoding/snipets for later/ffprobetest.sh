#!/bin/bash

 ffprobe -v quiet -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 test.mkv

ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 pythontest.mkv
 
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 pythontest.mkv

ffprobe -v error  -select_streams s:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 pythontest.mkv




vcodec = sp.run(shlex.split(f'ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {video}'), capture_output=True).stdout

acodec = sp.run(shlex.split(f'ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {video}'), capture_output=True).stdout

scodec = sp.run(shlex.split(f'ffprobe -v error -select_streams s:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {video}'), capture_output=True).stdout
