==== FFPROBE ====

ffmpeg -hide_banner -loglevel 16 -stats -r 24 -i newtest.mkv -r 24 -i newtestsrtlaopus.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -

====

OPUS Audio:
ffmpeg -hide_banner -loglevel 16 -stats -i INPUT.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt -c:a libopus OUTPUT.mkv

===


hvec nvec text:
ffmpeg -i test.mkv -c:v hevc_nvenc -crf 20 -keyint 240 -pix_fmt yuv420p10le test_nvec_crf20.mkv


---




for filename in os.listdir(path):
    if (filename.endswith(".mp4")): #or .avi, .mpeg, whatever.
        os.system(f'ffmpeg -i {filename} -f image2 -vf fps=fps=1 output%d.png')
    else:
        continue