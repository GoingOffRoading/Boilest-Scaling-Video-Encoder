import os
from pathlib import Path

__all__ = ["get_output_path"]


def get_output_path(out_file_name):
    """
    Append /Boil/Boil_Hold to the output file name to create the full output path.
    
    Args:
        out_file_name (str): The output filename
        
    Returns:
        str: The full path with /Boil/Boil_Hold prepended
    """
    output_path = os.path.join("Boil", "Boil_Hold", out_file_name)
    return output_path
