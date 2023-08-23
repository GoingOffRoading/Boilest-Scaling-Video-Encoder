import subprocess

result = subprocess.run(["ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt -c:a libopus testsrtlaopusasd.mkv"], shell=True, capture_output=True, text=True)

print(result.stdout)



# importing os module 
import os 
  
# Command to execute
cmd = 'ffmpeg -r 24 -i test.mkv -r 24 -i testsrtlaopus111.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -'
  
# Using os.system() method
os.system(cmd)