import subprocess

process = subprocess.Popen(
    ['ffmpeg', '--help'],
    stderr=subprocess.PIPE,
    text=True,
)

print(process.stderr.read())
