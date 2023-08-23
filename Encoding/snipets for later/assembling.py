#!/usr/bin/env python3                                                                            
import subprocess

# Define command and options wanted
command = "ffmpeg i"
options1 = "-c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le"
options2 = "-c:s srt"
options3 = "-c:a libopus"

# Ask user for file name(s) - now it's safe from shell injection
filename = input("Please introduce name(s) of file(s) of interest:\n")

# Create list with arguments for subprocess.run
args=[]
args.append(command)
args.append(options1)
for i in filename.split():
    args.append(i)
    
# Run subprocess.run and save output object
output = subprocess.run(args,capture_output=True)
print('###############')
print('Return code:', output.returncode)

# use decode function to convert to string
print('Output:',output.stdout.decode("utf-8"))