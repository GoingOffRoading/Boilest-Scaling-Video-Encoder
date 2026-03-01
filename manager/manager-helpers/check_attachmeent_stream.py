def check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """Checks the attachment stream from check_codecs to determine if the stream needs encoding."""
    # This will be populated at a later date
    #desired_attachment_codec = '???'
    #if codec_name != desired_attachment_codec:
    #    encoding_decision = True
    # Note, attachments may not have a codec name if the attachment is an image
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
    return encoding_decision, ffmpeg_command
