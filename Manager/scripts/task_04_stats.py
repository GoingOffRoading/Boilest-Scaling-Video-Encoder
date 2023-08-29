import subprocess

def ffstatrecorder(FILEPATH):
    command = subprocess.Popen(
        ['ffmpeg',
        '-i', 'test.mkv',
        '-vcodec', 'libsvtav1',
        '-crf', '20',
        '-preset', '5',
        '-g', '240',
        '-pix_fmt', 'yuv420p10le',
        '-c:s', 'srt',
        '-c:a', 'libopus',
        'pythontest.mkv'],
        stderr=subprocess.PIPE,
        text=True)

    print(command.stderr.read())


