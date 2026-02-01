import os
import subprocess
import logging


def validate_video(output_file_name):
    try:
        file_path = os.path.join("/boil/boil_hold/", output_file_name)
        print(file_path)
        command = 'ffmpeg -v error -i "' + file_path + '" -f null -'
        print(command)
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout or result.stderr:
            logging.debug('File failed video integrity check')
            return False
        else:
            logging.debug('File passed video integrity check')
            return True
    except Exception as e:
        logging.debug(f"Error during video integrity check: {e}")
        return False
