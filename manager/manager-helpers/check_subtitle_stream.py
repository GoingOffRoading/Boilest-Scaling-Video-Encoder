import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """Checks the subtitle stream from check_codecs to determine if the stream needs encoding."""
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_subtitle_codec = 'srt'
    #if codec_name != desired_subtitle_codec:
    #    encoding_decision = True
    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
    return encoding_decision, ffmpeg_command
