import os
import logging

__all__ = ["file_exists"]


def file_exists(filepath):
    """
    Check to see if the file that was scanned by the manager exists in the expected location.
    
    Returns:
        True if the file exists, False otherwise
    """
    try:
        if os.path.isfile(filepath):
            print('File passed existence check')
            return True
        else:
            print('File failed existence check')
            return False
    except Exception as e:
        print(f"Error checking file existence: {e}")
        logging.debug(f"Error checking file existence: {e}")
        return False
