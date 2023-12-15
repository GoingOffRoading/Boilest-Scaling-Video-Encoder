import subprocess

def run_ffmpeg(input_file, output_file, ffmpeg_args):
    cmd = ['ffmpeg', '-i', input_file] + ffmpeg_args + [output_file]

    try:
        # Start the FFmpeg process with stdout and stderr as pipes
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Stream stdout and stderr in real-time
        for line in process.stdout:
            print(f"STDOUT: {line.strip()}")

        for line in process.stderr:
            print(f"STDERR: {line.strip()}")

        # Wait for the process to complete
        exit_code = process.wait()

        print("FFmpeg encoding completed")
        return exit_code

    except Exception as e:
        print(f"Error: {e}")
        return 1  # Return a non-zero exit code to indicate an error

if __name__ == "__main__":
    input_file = "path/to/your/input.mp4"
    output_file = "path/to/your/output.mp4"
    ffmpeg_args = ["-c:v", "libx264", "-c:a", "aac", "-strict", "experimental"]

    exit_code = run_ffmpeg(input_file, output_file, ffmpeg_args)

    if exit_code == 0:
        print("Encoding was successful.")
    else:
        print(f"Encoding failed with exit code {exit_code}")
