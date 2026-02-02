import os
import time
import logging
from local_worker_functions import *

# Get log level from environment variable (default: INFO)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

__all__ = ["run_local_worker_loop"]

def run_local_worker_loop():
    poll_interval = int(os.environ.get("POLL_INTERVAL", "300"))
    logging.info(f"Worker started. Poll interval: {poll_interval} seconds")
    
    while True:
        try:
            time.sleep(poll_interval)
            
            logging.info("=" * 80)
            logging.info("Polling for new task...")
            
            # Step 1: Get largest task from queue
            status, response = get_largest_task()
            
            if status != 200:
                logging.error(f"✗ Failed to get task. Status: {status}, Response: {response}")
                continue
            
            if not response.get('success') or response.get('data') is None:
                logging.info("No tasks available in queue")
                continue
            
            task_data = response['data']
            file_guid = task_data.get('file_guid')
            directory_path = task_data.get('directory_path')
            input_file_name = task_data.get('input_file_name')
            output_file_name = task_data.get('output_file_name')
            before_file_size = task_data.get('before_file_size')
            ffmpeg_command = task_data.get('ffmpeg_string')

            after_file_size = 0

            before_file_size_file_path = os.path.join(directory_path, input_file_name)
            templorary_file_path = os.path.join("/boil/boil_hold/", output_file_name)
            after_file_path = os.path.join(directory_path, output_file_name)

            logging.info(f"Task received: {file_guid}")
            logging.info(f"  Input: {directory_path}/{input_file_name}")
            
            # Step 2: Preflight check - validate file hasn't changed and has integrity
            logging.info("Running preflight check...")
            
            # Step 3: Validate file size hasn't changed
            logging.info(f"Validating filehash for: {input_file_name}...")
            if not validate_hash(before_file_size_file_path, before_file_size):
                logging.error(f"✗ Preflight video hash check: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: Hash mismatch')
                continue
            logging.info(f"✓ Preflight video hash check: {input_file_name} PASSED")
            
            # Step 4: Validate video integrity
            logging.info(f"Validating video integrity for: {input_file_name}...")
            if not validate_video(before_file_size_file_path):
                logging.error(f"✗ Preflight video integrity check: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: Input Integrity')
                continue
            logging.info(f"✓ Preflight video integrity check: {input_file_name} PASSED")
            
            # Step 5: Run ffmpeg encoding
            logging.info(f"Starting ffmpeg encoding for: {input_file_name}...")
            if not run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path):
                logging.error(f"✗ FFmpeg encoding: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: FFmpeg failure')
                continue
            logging.info(f"✓ FFmpeg encoding: {input_file_name} PASSED")
            
            # Step 6: Postflight check - validate output video integrity
            logging.info(f"Running postflight check for: {input_file_name}...")
            if not validate_post_flight_video(templorary_file_path):
                logging.error(f"✗ Postflight video integrity check: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: Postflight Integrity')
                continue
            logging.info(f"✓ Postflight video integrity check: {input_file_name} PASSED")

            # Step 7: Get output file size
            logging.info(f"Getting output file size for: {input_file_name}...")
            after_file_size = get_file_size_kb(templorary_file_path)
            if after_file_size == 0:
                logging.error(f"✗ Postflight file size check: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: Postflight file size check')
                continue
            logging.info(f"✓ Output file size: {after_file_size} KB")

            # Step 8: Delete source
            logging.info(f"Deleting source file: {input_file_name}...")
            if not delete_file(before_file_size_file_path):
                logging.error(f"✗ Postflight delete source file: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: Postflight delete source file')
                continue
            logging.info(f"✓ Postflight delete source: {input_file_name} PASSED")

            # Step 9: Move temporary file to final destination
            logging.info(f"Moving temporary file to final destination for: {input_file_name}...")
            if not move_file(templorary_file_path, after_file_path):
                logging.error(f"✗ Postflight move temporary file to final destination: {input_file_name} FAILED")
                report_encoding_completed(file_guid, 'Failed: Postflight move temporary file to final destination')
                continue
            logging.info(f"✓ Postflight move temporary file to final destination: {input_file_name} PASSED")

            # Step 10: Report completion to manager
            logging.info("Reporting completion to manager...")
            report_status, report_response = report_encoding_completed(file_guid, 'encoded', after_file_size)
            if report_status != 200:
                logging.error(f"✗ Failed to report completion. Status: {report_status}, Response: {report_response}")
                # Note: Even if reporting fails, the file has been processed successfully
            else:
                logging.info("✓ Completion reported successfully")
            
            logging.info(f"Task {file_guid} completed successfully!")
            logging.info("=" * 80)
            
        except KeyboardInterrupt:
            logging.info("Worker stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error in worker loop: {type(e).__name__}: {str(e)}")
        

if __name__ == "__main__":
    run_local_worker_loop()
