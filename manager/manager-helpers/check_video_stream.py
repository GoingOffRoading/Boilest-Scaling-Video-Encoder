import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def check_video_stream(encoding_decision, i, stream_info, ffmpeg_command, ffmpeg_video, desired_video_codec):
    """Checks the video stream from check_codecs to determine if the stream needs encoding."""
    codec_name = stream_info['streams'][i]['codec_name'] 

    # Check for HDR metadata and BT.2020 color space, which may require encoding to preserve HDR quality
    color_transfer = stream_info['streams'][i].get('color_transfer', '')
    color_primaries = stream_info['streams'][i].get('color_primaries', '')
    color_space = stream_info['streams'][i].get('color_space', '')
    side_data_list = stream_info['streams'][i].get('side_data_list', [])

    has_hdr_transfer = color_transfer in ('smpte2084', 'arib-std-b67')
    has_bt2020 = color_primaries == 'bt2020' or color_space in ('bt2020nc', 'bt2020c')
    has_hdr_metadata = (
        any('Mastering display' in sd.get('side_data_type', '') for sd in side_data_list)
        or any('Content light' in sd.get('side_data_type', '') for sd in side_data_list)
    )
    is_hdr = has_hdr_transfer or (has_bt2020 and has_hdr_metadata)

    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    if codec_name == desired_video_codec:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name == 'mjpeg':
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif is_hdr:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name != desired_video_codec: 
        encoding_decision = True
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + ffmpeg_video
    else:
        logging.debug('ignoring for now')
    return encoding_decision, ffmpeg_command
