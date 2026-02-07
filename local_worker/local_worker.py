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
            
            # Step 0: Get largest task from queue
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
            
            logging.info(f"Running preflight checks on: {input_file_name}")

            
            # Step 1: Validate file existence
            if not file_exists(before_file_size_file_path):
                logging.error(f"✗ Step 1: File existence validation failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: File not found')
                continue
            logging.info(f"✓ Step 1: File existence validated")


            # Step 2: Validate file size hasn't changed
            if not validate_hash(before_file_size_file_path, before_file_size):
                logging.error(f"✗ Step 2: File hash validation failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: Hash mismatch')
                continue
            logging.info(f"✓ Step 2: File hash validated")
            

            # Step 3: Validate video integrity
            if not validate_video_full(before_file_size_file_path):
                logging.error(f"✗ Step 3: Video integrity check failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: Input Integrity')
                continue
            logging.info(f"✓ Step 3: Video integrity validated")
            

            logging.info(f"Preflight checks passed... Starting FFmpeg on: {input_file_name}")


            # Step 4: Run ffmpeg encoding
            if not run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path):
                logging.error(f"✗ Step 4: FFmpeg encoding failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: FFmpeg failure')
                continue
            logging.info(f"✓ Step 4: FFmpeg encoding completed")


            logging.info(f"FFmpeg completed... Starting postflight checks on: {input_file_name}")
            

            # Step 5: Validate temporary file existence
            if not file_exists(templorary_file_path):
                logging.error(f"✗ Step 5: Temporary file existence validation failed for: {output_file_name}")
                report_encoding_completed(file_guid, 'Failed: Temporary file not found')
                continue
            logging.info(f"✓ Step 5: Temporary file existence validated")



            # Step 6: Postflight check - validate output video integrity
            if not validate_video_full(templorary_file_path):
                logging.error(f"✗ Step 6: Output video integrity check failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: Postflight Integrity')
                continue
            logging.info(f"✓ Step 6: Output video integrity validated")


            logging.info(f"Postflight checks passed... Starting postflight workflow on: {input_file_name}")


            # Step 7: Get output file size
            after_file_size = get_file_size_kb(templorary_file_path)
            if after_file_size == 0:
                logging.error(f"✗ Step 7: File size check failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: Postflight file size check')
                continue
            logging.info(f"✓ Step 7: Output file size captured")


            # Step 8: Delete source
            if not delete_file(before_file_size_file_path):
                logging.error(f"✗ Step 8: Source file deletion failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: Postflight delete source file')
                continue
            logging.info(f"✓ Step 8: Source file deleted")


            # Step 9: Move temporary file to final destination
            if not move_file(templorary_file_path, after_file_path):
                logging.error(f"✗ Step 9: File move failed for: {input_file_name}")
                report_encoding_completed(file_guid, 'Failed: Postflight move temporary file to final destination')
                continue
            logging.info(f"✓ Step 9: File moved to final destination")


            # Step 10: Report completion to manager
            report_status, report_response = report_encoding_completed(file_guid, 'encoded', after_file_size)
            if report_status != 200:
                logging.error(f"✗ Step 10: Failed to report completion. Status: {report_status}, Response: {report_response}")
                # Note: Even if reporting fails, the file has been processed successfully
            else:
                logging.info("✓ Step 10: Completion reported successfully")
            

            logging.info(f"Task {input_file_name} encoded successfully!")
            logging.info("=" * 80)
            
        except KeyboardInterrupt:
            logging.info("Worker stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error in worker loop: {type(e).__name__}: {str(e)}")
        

if __name__ == "__main__":
    run_local_worker_loop()
