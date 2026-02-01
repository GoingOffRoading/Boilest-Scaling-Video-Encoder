import subprocess
import os


def run_ffmpeg(directory_path, input_file_name, ffmpeg_command, output_file_name):
    """
    Accepts the output of get_record and runs ffmpeg.
    Returns (success, result) where result is the full subprocess.CompletedProcess.

    Expected record keys:
      - directory_path
      - input_file_name
      - output_file_name
    """
    try:
        ffmpeg_settings = 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i'

        input_path = os.path.join(directory_path, input_file_name)
        output_path = os.path.join("/boil/boil_hold", output_file_name)

        print(input_path)
        print(output_path)
        
        command = f"{ffmpeg_settings} \"{input_path}\" {ffmpeg_command} \"{output_path}\""

        print(command)

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in process.stdout:
            print(line)
        return True
    except Exception as exc:
        print(f"Error: {exc}")
        return False  # Return a non-zero exit code to indicate an error
