





Setting the timezone

Use the TZ identifier here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

ffmpeg -hide_banner -loglevel 16 -stats -r 24 -i newtest.mkv -r 24 -i newtestsrtlaopus.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -


ffmpeg -video_size 3840x2160 -framerate 60 -pixel_format yuv420p10le -i decoded_encoded_h264_55.YUV -video_size 3840x2160 -framerate 60 -pixel_format yuv420p10le -i S01AirAcrobatic_3840x2160_60fps_10bit_420.yuv -lavfi libvmaf="model_path=vmaf_v0.6.1.pkl:log_path=VMAF.txt" -f null -