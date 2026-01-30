import subprocess
import logging

__all__ = ["validate_video"]


def validate_video(filepath):
    """
    Determine if a video is valid, or if the video contains errors.
    There is no point in encoding video if the video is corrupt.
    
    Uses ffmpeg to validate the video stream integrity.
    
    Returns:
        True if the video is valid, False if validation fails or errors detected
    """
    try:
        command = 'ffmpeg -v error -i "' + filepath + '" -f null -'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout or result.stderr:
            print('File failed validation check')
            return False
        else:
            print('File passed validation check')
            return True
    except Exception as e:
        print(f"Error during validation check: {e}")
        logging.debug(f"Error during validation check: {e}")
        return False
