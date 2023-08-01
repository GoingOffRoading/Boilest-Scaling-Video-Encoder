ffmpeg -i test.mkv -i testcrf20preset510bitactual.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -



ffmpeg -i test.mkv -c:v libsvtav1 -crf 20 -preset 5 -keyint 240 -pix_fmt yuv420p10le testcrf20preset510bitactual.mkv

