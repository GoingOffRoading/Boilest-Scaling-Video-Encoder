import os
import time
import random
import logging
from local_worker_functions import *

# Get log level from environment variable (default: INFO)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

__all__ = ["run_local_worker_loop"]

def run_local_worker_loop():
    logging.info("Worker started. Polling for tasks...")
    
    while True:
        try:
            poll_sleep_seconds = random.uniform(0, 15)
            logging.info(f"Sleeping {poll_sleep_seconds:.2f}s before next poll")
            time.sleep(poll_sleep_seconds)
            
            logging.info("=" * 80)
            logging.info("Polling for new task...")
            
            # Step 0: Get largest task from queue
            status, response = get_largest_task()
            
            if status != 200:
                logging.error(f"✗ Failed to get task. Status: {status}, Response: {response}")
                logging.info("Sleeping 300s before retry after manager request failure")
                time.sleep(300)
                continue
            
            if not response.get('success') or response.get('data') is None:
                logging.info("No tasks available in queue")
                logging.info("Sleeping 300s before polling again")
                time.sleep(300)
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
            step_1_start_epoch = time.time()
            step_1_start_perf = time.perf_counter()
            logging.info(f"Step 1 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_1_start_epoch))}")
            if not file_exists(before_file_size_file_path):
                logging.error(f"✗ Step 1: File existence validation failed for: {input_file_name}")
                step_1_duration = time.perf_counter() - step_1_start_perf
                logging.info(f"Step 1 outcome: failed (duration: {format_duration(step_1_duration)})")
                report_encoding_completed(file_guid, 'Failed: File not found')
                continue
            logging.info(f"✓ Step 1: File existence validated")
            step_1_duration = time.perf_counter() - step_1_start_perf
            logging.info(f"Step 1 outcome: passed (duration: {format_duration(step_1_duration)})")


            # Step 2: Validate file size hasn't changed
            step_2_start_epoch = time.time()
            step_2_start_perf = time.perf_counter()
            logging.info(f"Step 2 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_2_start_epoch))}")
            if not validate_hash(before_file_size_file_path, before_file_size):
                logging.error(f"✗ Step 2: File hash validation failed for: {input_file_name}")
                step_2_duration = time.perf_counter() - step_2_start_perf
                logging.info(f"Step 2 outcome: failed (duration: {format_duration(step_2_duration)})")
                report_encoding_completed(file_guid, 'Failed: Hash mismatch')
                continue
            logging.info(f"✓ Step 2: File hash validated")
            step_2_duration = time.perf_counter() - step_2_start_perf
            logging.info(f"Step 2 outcome: passed (duration: {format_duration(step_2_duration)})")
            

            # Step 3: Validate video integrity
            step_3_start_epoch = time.time()
            step_3_start_perf = time.perf_counter()
            logging.info(f"Step 3 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_3_start_epoch))}")
            if not validate_video_full(before_file_size_file_path, 15):
                logging.error(f"✗ Step 3: Video integrity check failed for: {input_file_name}")
                step_3_duration = time.perf_counter() - step_3_start_perf
                logging.info(f"Step 3 outcome: failed (duration: {format_duration(step_3_duration)})")
                report_encoding_completed(file_guid, 'Failed: Input Integrity')
                continue
            logging.info(f"✓ Step 3: Video integrity validated")
            step_3_duration = time.perf_counter() - step_3_start_perf
            logging.info(f"Step 3 outcome: passed (duration: {format_duration(step_3_duration)})")
            

            logging.info(f"Preflight checks passed... Starting FFmpeg on: {input_file_name}")


            # Step 4: Run ffmpeg encoding
            step_4_start_epoch = time.time()
            step_4_start_perf = time.perf_counter()
            logging.info(f"Step 4 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_4_start_epoch))}")
            if not run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path):
                logging.error(f"✗ Step 4: FFmpeg encoding failed for: {input_file_name}")
                step_4_duration = time.perf_counter() - step_4_start_perf
                logging.info(f"Step 4 outcome: failed (duration: {format_duration(step_4_duration)})")
                report_encoding_completed(file_guid, 'Failed: FFmpeg failure')
                continue
            logging.info(f"✓ Step 4: FFmpeg encoding completed")
            step_4_duration = time.perf_counter() - step_4_start_perf
            logging.info(f"Step 4 outcome: passed (duration: {format_duration(step_4_duration)})")


            logging.info(f"FFmpeg completed... Starting postflight checks on: {input_file_name}")
            

            # Step 5: Validate temporary file existence
            step_5_start_epoch = time.time()
            step_5_start_perf = time.perf_counter()
            logging.info(f"Step 5 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_5_start_epoch))}")
            if not file_exists(templorary_file_path):
                logging.error(f"✗ Step 5: Temporary file existence validation failed for: {output_file_name}")
                step_5_duration = time.perf_counter() - step_5_start_perf
                logging.info(f"Step 5 outcome: failed (duration: {format_duration(step_5_duration)})")
                report_encoding_completed(file_guid, 'Failed: Temporary file not found')
                continue
            logging.info(f"✓ Step 5: Temporary file existence validated")
            step_5_duration = time.perf_counter() - step_5_start_perf
            logging.info(f"Step 5 outcome: passed (duration: {format_duration(step_5_duration)})")



            # Step 6: Postflight check - validate output video integrity
            step_6_start_epoch = time.time()
            step_6_start_perf = time.perf_counter()
            logging.info(f"Step 6 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_6_start_epoch))}")
            if not post_flight_validate_video_full(templorary_file_path):
                logging.error(f"✗ Step 6: Output video integrity check failed for: {input_file_name}")
                step_6_duration = time.perf_counter() - step_6_start_perf
                logging.info(f"Step 6 outcome: failed (duration: {format_duration(step_6_duration)})")
                report_encoding_completed(file_guid, 'Failed: Postflight Integrity')
                continue
            logging.info(f"✓ Step 6: Output video integrity validated")
            step_6_duration = time.perf_counter() - step_6_start_perf
            logging.info(f"Step 6 outcome: passed (duration: {format_duration(step_6_duration)})")


            logging.info(f"Postflight checks passed... Starting postflight workflow on: {input_file_name}")


            # Step 7: Get output file size
            step_7_start_epoch = time.time()
            step_7_start_perf = time.perf_counter()
            logging.info(f"Step 7 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_7_start_epoch))}")
            after_file_size = get_file_size_kb(templorary_file_path)
            if after_file_size == 0:
                logging.error(f"✗ Step 7: File size check failed for: {input_file_name}")
                step_7_duration = time.perf_counter() - step_7_start_perf
                logging.info(f"Step 7 outcome: failed (duration: {format_duration(step_7_duration)})")
                report_encoding_completed(file_guid, 'Failed: Postflight file size check')
                continue
            logging.info(f"✓ Step 7: Output file size captured")
            step_7_duration = time.perf_counter() - step_7_start_perf
            logging.info(f"Step 7 outcome: passed (duration: {format_duration(step_7_duration)})")


            # Step 8: Delete source
            step_8_start_epoch = time.time()
            step_8_start_perf = time.perf_counter()
            logging.info(f"Step 8 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_8_start_epoch))}")
            if not delete_file(before_file_size_file_path):
                logging.error(f"✗ Step 8: Source file deletion failed for: {input_file_name}")
                step_8_duration = time.perf_counter() - step_8_start_perf
                logging.info(f"Step 8 outcome: failed (duration: {format_duration(step_8_duration)})")
                report_encoding_completed(file_guid, 'Failed: Postflight delete source file')
                continue
            logging.info(f"✓ Step 8: Source file deleted")
            step_8_duration = time.perf_counter() - step_8_start_perf
            logging.info(f"Step 8 outcome: passed (duration: {format_duration(step_8_duration)})")


            # Step 9: Move temporary file to final destination
            step_9_start_epoch = time.time()
            step_9_start_perf = time.perf_counter()
            logging.info(f"Step 9 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_9_start_epoch))}")
            if not move_file(templorary_file_path, after_file_path):
                logging.error(f"✗ Step 9: File move failed for: {input_file_name}")
                step_9_duration = time.perf_counter() - step_9_start_perf
                logging.info(f"Step 9 outcome: failed (duration: {format_duration(step_9_duration)})")
                report_encoding_completed(file_guid, 'Failed: Postflight move temporary file to final destination')
                continue
            logging.info(f"✓ Step 9: File moved to final destination")
            step_9_duration = time.perf_counter() - step_9_start_perf
            logging.info(f"Step 9 outcome: passed (duration: {format_duration(step_9_duration)})")


            # Step 10: Report completion to manager
            step_10_start_epoch = time.time()
            step_10_start_perf = time.perf_counter()
            logging.info(f"Step 10 started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(step_10_start_epoch))}")
            report_status, report_response = report_encoding_completed(file_guid, 'encoded', after_file_size)
            if report_status != 200:
                logging.error(f"✗ Step 10: Failed to report completion. Status: {report_status}, Response: {report_response}")
                # Note: Even if reporting fails, the file has been processed successfully
                step_10_duration = time.perf_counter() - step_10_start_perf
                logging.info(f"Step 10 outcome: failed (duration: {format_duration(step_10_duration)})")
            else:
                logging.info("✓ Step 10: Completion reported successfully")
                step_10_duration = time.perf_counter() - step_10_start_perf
                logging.info(f"Step 10 outcome: passed (duration: {format_duration(step_10_duration)})")
            

            logging.info(f"Task {input_file_name} encoded successfully!")
            logging.info("=" * 80)
            
        except KeyboardInterrupt:
            logging.info("Worker stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error in worker loop: {type(e).__name__}: {str(e)}")
        

if __name__ == "__main__":
    run_local_worker_loop()
