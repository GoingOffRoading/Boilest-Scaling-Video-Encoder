ffmpeg -r 24 -i test.mkv -r 24 -i testsrtlaopus111.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -



ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -keyint 240 -pix_fmt yuv420p10le testcrf20preset510bitactual.mkv

keyframes test:
ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le testkeyframesl.mkv

And now change subtitle format:
ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt testsrtl.mkv

===

OPUS Audio:
ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt -c:a libopus testsrtlaopus.mkv

===


hvec nvec text:
ffmpeg -i test.mkv -c:v hevc_nvenc -crf 20 -keyint 240 -pix_fmt yuv420p10le test_nvec_crf20.mkv


ffmpeg -i test.mkv testsrtlaopus111.mkv



---




for filename in os.listdir(path):
    if (filename.endswith(".mp4")): #or .avi, .mpeg, whatever.
        os.system(f'ffmpeg -i {filename} -f image2 -vf fps=fps=1 output%d.png')
    else:
        continue