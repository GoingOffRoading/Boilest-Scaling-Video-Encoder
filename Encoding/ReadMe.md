ffmpeg -r 24 -i test.mkv -r 24 -i testcrf20preset510bitactual.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -



ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -keyint 240 -pix_fmt yuv420p10le testcrf20preset510bitactual.mkv

keyframes test:
ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le testkeyframesl.mkv

And now change subtitle format:
ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt testsrtl.mkv

OPUS Audio:
ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt -c:a libopus testsrtlaopus.mkv

hvec nvec text:


ffmpeg -i test.mkv -c:v hevc_nvenc -crf 20 -keyint 240 -pix_fmt yuv420p10le test_nvec_crf20.mkv