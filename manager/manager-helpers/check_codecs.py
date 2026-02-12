import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def check_codecs(encoding_decision, stream_info, ffmpeg_command, ffmpeg_video, desired_video_codec):
    """Check codecs in streams and build ffmpeg command."""
    from check_video_stream import check_video_stream
    from check_audio_stream import check_audio_stream
    from check_subtitle_stream import check_subtitle_stream
    from check_attachmeent_stream import check_attachmeent_stream
    
    streams_count = stream_info['format']['nb_streams']
    
    for i in range(0, streams_count):
        codec_type = stream_info['streams'][i]['codec_type'] 
        if codec_type == 'video':
            logging.debug('Stream ' + str(i) + ' is video')
            encoding_decision, ffmpeg_command = check_video_stream(
                encoding_decision,
                i,
                stream_info,
                ffmpeg_command,
                ffmpeg_video,
                desired_video_codec,
            )
        elif codec_type == 'audio':
            encoding_decision, ffmpeg_command = check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command)
            logging.debug('audio stream')
        elif codec_type == 'subtitle':
            encoding_decision, ffmpeg_command = check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command)
            logging.debug('subtitle stream')
        elif codec_type == 'attachment':
            encoding_decision, ffmpeg_command = check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command) 
            logging.debug('attachment stream')    
    logging.debug(encoding_decision)   
    logging.debug(ffmpeg_command)
    return encoding_decision, ffmpeg_command
