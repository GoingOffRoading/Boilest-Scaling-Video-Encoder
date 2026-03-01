import os
import logging
import sys

# Add parent directory to path to import db_path module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db_path import get_db_path
from get_all_directories import get_all_directories
from find_video_files import find_video_files
from is_file_unpulled_in_queue import is_file_unpulled_in_queue
from run_ffprobe import run_ffprobe
from output_file_name_fx import output_file_name_fx
from check_codecs import check_codecs
from get_file_size_kb import get_file_size_kb
from write_to_queue import write_to_queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run_queue_workflow(db_path=None, extensions=None):
    """Main workflow to scan directories and queue files for encoding."""
    db_path = get_db_path()

    logging.debug(db_path)

    directories = get_all_directories(db_path)
    
    for directory_guid, directory_path, ffmpeg_video, desired_video_codec in directories:
        logging.info(f"\nScanning directory {directory_path} (guid={directory_guid})")
        for directory, input_file_name in find_video_files(directory_path):
            file_path = os.path.join(directory, input_file_name)
            logging.debug(f"  Found: {file_path}")
            if is_file_unpulled_in_queue(input_file_name, directory, db_path) == False:
                default_encoding_decision = False
                ffmpeg_command = ''
                probe_data = run_ffprobe(directory, input_file_name)
                output_file_name, file_encoding_decision = output_file_name_fx(input_file_name, default_encoding_decision)
                final_encoding_decision, ffmpeg_command = check_codecs(
                    file_encoding_decision,
                    probe_data,
                    ffmpeg_command,
                    ffmpeg_video,
                    desired_video_codec,
                )
                
                logging.debug(final_encoding_decision)
                logging.debug(ffmpeg_command)
                logging.debug(output_file_name)

                if final_encoding_decision == True:
                    logging.info(f"    Adding to queue: {input_file_name}")
                    before_file_size = get_file_size_kb(directory, input_file_name)
                    file_guid = write_to_queue(directory_guid, directory, input_file_name, output_file_name, before_file_size, ffmpeg_command, db_path)
                    logging.debug(f"    Queued file_guid: {file_guid}")
                else:
                    logging.debug(f"    Skiping: {input_file_name}")


if __name__ == "__main__":
    run_queue_workflow()
