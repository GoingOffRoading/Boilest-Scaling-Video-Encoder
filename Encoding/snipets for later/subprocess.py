import subprocess

result = subprocess.run(["ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le -c:s srt -c:a libopus testsrtlaopusasd.mkv"], shell=True, capture_output=True, text=True)

print(result.stdout)

