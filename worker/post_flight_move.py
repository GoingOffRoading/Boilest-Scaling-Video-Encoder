import os
import logging
import shutil
from pathlib import Path


def get_file_size_kb(output_file_name):
    try:
        file_path = os.path.join("/boil/boil_hold/", output_file_name)
        print(file_path)
        file_size_bytes = Path(file_path).stat().st_size
        file_size_kb = int(file_size_bytes / 1024)
        return file_size_kb
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return 0
    except Exception as e:
        logging.debug(f"✗ Error getting file size: {e}")
        return 0


def delete_file(directory_path, input_file_name):
    try:
        file_path = os.path.join(directory_path, input_file_name)
        print(f"Deleting file: {file_path}")
        os.remove(file_path)
        logging.debug(f"✓ File deleted successfully: {file_path}")
        return True
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return False
    except Exception as e:
        logging.debug(f"✗ Error deleting file: {e}")
        return False


def move_file(output_file_name, destination_directory):
    try:
        source_path = os.path.join("/boil/boil_hold/", output_file_name)
        destination_path = os.path.join(destination_directory, output_file_name)
        print(f"Moving file from {source_path} to {destination_path}")
        shutil.move(source_path, destination_path)
        logging.debug(f"✓ File moved successfully: {source_path} -> {destination_path}")
        return True
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {source_path}")
        return False
    except Exception as e:
        logging.debug(f"✗ Error moving file: {e}")
        return False


def process_file(directory_path, input_file_name, output_file_name):
    """
    Orchestrates the post-flight file processing workflow.
    1. Gets the file size of the output file
    2. If successful, deletes the input file
    3. If successful, moves the output file to the directory
    
    Returns: (success, file_size) tuple
    """
    try:
        # Step 1: Get file size of output file
        print(f"Step 1: Getting file size for {output_file_name}")
        file_size = get_file_size_kb(output_file_name)
        if file_size == 0:
            logging.debug("✗ Failed to get file size")
            return (False, 0)
        print(f"✓ File size: {file_size} KB")
        
        # Step 2: Delete input file
        print(f"Step 2: Deleting input file {input_file_name}")
        if not delete_file(directory_path, input_file_name):
            logging.debug("✗ Failed to delete input file")
            return (False, file_size)
        print("✓ Input file deleted")
        
        # Step 3: Move output file
        print(f"Step 3: Moving output file to {directory_path}")
        if not move_file(output_file_name, directory_path):
            logging.debug("✗ Failed to move output file")
            return (False, file_size)
        print("✓ Output file moved")
        
        logging.debug("✓ All operations completed successfully")
        return (True, file_size)
        
    except Exception as e:
        logging.debug(f"✗ Error in process_file: {e}")
        return (False, 0)
