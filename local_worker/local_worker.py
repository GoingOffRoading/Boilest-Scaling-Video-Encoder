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
            
            # Step 0: Get task from queue
            status, response = get_task()
            
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
            
            # ===============================================================
            # =                       Preflight Checks                      =
            # ===============================================================


            logging.info(f"Running preflight checks on: {input_file_name}")


            if not sleep_with_file_check(1, file_guid, check='no'):
                logging.info("Aborting current task due to manager stop (during initial sleep)")
                continue

            # Step 1: Validate file existence
            step_1_start_perf = time.perf_counter()
            exists, reason = file_exists(before_file_size_file_path)
            if not exists:
                step_1_duration = time.perf_counter() - step_1_start_perf
                logging.error(f"✗ Step 1: File existence validation failed for: {input_file_name} (duration: {format_duration(step_1_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: File Not Found', notes=reason)
                continue
            step_1_duration = time.perf_counter() - step_1_start_perf
            logging.info(f"✓ Step 1: File existence validated (duration: {format_duration(step_1_duration)})")


            if not sleep_with_file_check(1, file_guid, check='no'):
                logging.info("Aborting current task due to manager stop (after step 1)")
                continue


            # Step 2: Validate file size hasn't changed
            step_2_start_perf = time.perf_counter()
            valid_hash, reason = validate_hash(before_file_size_file_path, before_file_size)
            if not valid_hash:
                step_2_duration = time.perf_counter() - step_2_start_perf
                logging.error(f"✗ Step 2: File hash validation failed for: {input_file_name} (duration: {format_duration(step_2_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: Hash Mismatch', notes=reason)
                continue
            step_2_duration = time.perf_counter() - step_2_start_perf
            logging.info(f"✓ Step 2: File hash validated (duration: {format_duration(step_2_duration)})")

            if not sleep_with_file_check(1, file_guid, check='yes'):
                logging.info("Aborting current task due to manager stop (after step 2)")
                continue
            

            # ===============================================================
            # =                          Run FFmpeg                         =
            # ===============================================================

            logging.info(f"Preflight checks passed... Starting FFmpeg on: {input_file_name}")


            # Step 3: Run ffmpeg encoding
            step_4_start_perf = time.perf_counter()
            ffmpeg_success, ffmpeg_reason = run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path, file_guid=file_guid)
            if not ffmpeg_success:
                step_4_duration = time.perf_counter() - step_4_start_perf
                logging.error(f"✗ Step 4: FFmpeg encoding failed for: {input_file_name} (duration: {format_duration(step_4_duration)}) Reason: {ffmpeg_reason}")
                # Check if the worker should stop before reporting failure
                if ffmpeg_reason == "Stopped by Manager":
                    logging.info("Aborting current task due to Stopped by Manageer")
                    continue
                else:                    
                    report_encoding_completed(file_guid, 'Failed: FFmpeg Failure', notes=ffmpeg_reason)
                    continue
            step_4_duration = time.perf_counter() - step_4_start_perf
            logging.info(f"✓ Step 4: FFmpeg encoding completed (duration: {format_duration(step_4_duration)})")

            if not sleep_with_file_check(1, file_guid, check='yes'):
                logging.info("Aborting current task due to manager stop (after ffmpeg)")
                continue


            # ===============================================================
            # =                     Postflight Checks                       =
            # ===============================================================

            logging.info(f"FFmpeg completed... Starting postflight checks on: {input_file_name}")
            

            # Step 4: Validate temporary file existence
            step_4_start_perf = time.perf_counter()
            exists, reason = file_exists(templorary_file_path)
            if not exists:
                step_4_duration = time.perf_counter() - step_4_start_perf
                logging.error(f"✗ Step 4: Temporary file existence validation failed for: {output_file_name} (duration: {format_duration(step_4_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: Temporary File Not Found', notes=reason)
                continue
            step_4_duration = time.perf_counter() - step_4_start_perf
            logging.info(f"✓ Step 4: Temporary file existence validated (duration: {format_duration(step_4_duration)})")


            if not sleep_with_file_check(1, file_guid, check='no'):
                logging.info("Aborting current task due to manager stop (after step 4)")
                continue


            # Step 5: Postflight check - validate output video integrity
            step_5_start_perf = time.perf_counter()
            is_valid, reason = post_flight_validate_video_full(templorary_file_path)
            if not is_valid:
                step_5_duration = time.perf_counter() - step_5_start_perf
                logging.error(f"✗ Step 5: Output video integrity check failed for: {input_file_name} (duration: {format_duration(step_5_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: Postflight Integrity', notes=reason)
                continue
            step_5_duration = time.perf_counter() - step_5_start_perf
            logging.info(f"✓ Step 5: Output video integrity validated (duration: {format_duration(step_5_duration)})")


            if not sleep_with_file_check(1, file_guid, check='yes'):
                logging.info("Aborting current task due to manager stop (after step 5)")
                continue


            # ===============================================================
            # =                     Postflight Workflow                     =
            # ===============================================================


            logging.info(f"Postflight checks passed... Starting postflight workflow on: {input_file_name}")


            # Step 6: Get output file size
            step_6_start_perf = time.perf_counter()
            after_file_size, reason = get_file_size_kb(templorary_file_path)
            if after_file_size == 0:
                step_6_duration = time.perf_counter() - step_6_start_perf
                logging.error(f"✗ Step 6: File size check failed for: {input_file_name} (duration: {format_duration(step_6_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: Postflight File Size Check', notes=reason)
                continue
            step_6_duration = time.perf_counter() - step_6_start_perf
            logging.info(f"✓ Step 6: Output file size captured (duration: {format_duration(step_6_duration)})")


            if not sleep_with_file_check(1, file_guid, check='no'):
                logging.info("Aborting current task due to manager stop (after step 6)")
                continue


            # Step 7: Delete source
            step_7_start_perf = time.perf_counter()
            deleted, reason = delete_file(before_file_size_file_path)
            if not deleted:
                step_7_duration = time.perf_counter() - step_7_start_perf
                logging.error(f"✗ Step 7: Source file deletion failed for: {input_file_name} (duration: {format_duration(step_7_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: Postflight Delete Source File', notes=reason)
                continue
            step_7_duration = time.perf_counter() - step_7_start_perf
            logging.info(f"✓ Step 7: Source file deleted (duration: {format_duration(step_7_duration)})")


            if not sleep_with_file_check(1, file_guid, check='no'):
                logging.info("Aborting current task due to manager stop (after step 7)")
                continue


            # Step 8: Move temporary file to final destination
            step_8_start_perf = time.perf_counter()
            moved, reason = move_file(templorary_file_path, after_file_path)
            if not moved:
                step_8_duration = time.perf_counter() - step_8_start_perf
                logging.error(f"✗ Step 8: File move failed for: {input_file_name} (duration: {format_duration(step_8_duration)}) Reason: {reason}")
                report_encoding_completed(file_guid, 'Failed: Postflight Move Temporary File To Final Destination', notes=reason)
                continue
            step_8_duration = time.perf_counter() - step_8_start_perf
            logging.info(f"✓ Step 8: File moved to final destination (duration: {format_duration(step_8_duration)})")


            if not sleep_with_file_check(1, file_guid, check='no'):
                logging.info("Aborting current task due to manager stop (after step 8)")
                continue


            # Step 9: Report completion to manager
            step_9_start_perf = time.perf_counter()
            report_status, report_response = report_encoding_completed(file_guid, 'encoded', after_file_size=after_file_size, notes='Success')
            if report_status != 200:
                step_9_duration = time.perf_counter() - step_9_start_perf
                # Note: Even if reporting fails, the file has been processed successfully
                logging.error(f"✗ Step 9: Failed to report completion. Status: {report_status}, Response: {report_response} (duration: {format_duration(step_9_duration)})")
            else:
                step_9_duration = time.perf_counter() - step_9_start_perf
                logging.info(f"✓ Step 9: Completion reported successfully (duration: {format_duration(step_9_duration)})")
            

            logging.info(f"Task {input_file_name} encoded successfully!")
            logging.info("=" * 80)
            
        except KeyboardInterrupt:
            logging.info("Worker stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error in worker loop: {type(e).__name__}: {str(e)}")
        

if __name__ == "__main__":
    run_local_worker_loop()
