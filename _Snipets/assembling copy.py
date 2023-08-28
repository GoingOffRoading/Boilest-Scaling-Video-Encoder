#!/usr/bin/env python3                                                                            
import os
import subprocess
import time

os.chdir('C://Users/Chase/')

# Define command and options wanted
command = "ffmpeg -i test.mkv"
options1 = "-c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le"
options2 = "-c:s srt"
options3 = "-c:a libopus"
output = "test123.mkv"


# Create list with arguments for subprocess.run
args=[]
print (args)
time.sleep (1)
args.append(command)
print (args)
time.sleep (1)
args.append(options1)
print (args)
time.sleep (1)
args.append(options2)
print (args)
time.sleep (1)
args.append(options3)
print (args)
time.sleep (1)
args.append(output)
print (args)
time.sleep (1)

subprocess.call(args,shell=True)