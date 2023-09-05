# How to use Templates

The input templates have a relatively simple format:

    {
        "config_name": "default",
        "watch_folder": "/boil_watch",
        "container": "mkv",
        "container_ffmpeg_string": "matroska,webm",
        "video_codec": "AV1",
        "video_ffmpeg_string": "-c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le",
        "audio_codec": "OPUS",
        "audio_ffmpeg_string": "-c:a libopus",
        "subtitle_format": "SRT",
        "subtitle_ffmpeg_string": "-c:s srt"
    }

  - watch_folder is the folder Boilest will scan.  This will be whatever directory the media files in the container were mapped to
  - container is the video container or file extension that is desired
  - container_ffmpeg_string is the ffmpeg recognized variable for that container.