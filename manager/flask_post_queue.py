import sqlite3
import os
import uuid
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from db_path import get_db_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

logging.debug("Libraries imported successfully")

db_path = get_db_path()
logging.debug(f"Database path: {db_path}")

def get_all_directories(db_path):
    """Return all rows from the `directories` table as a list of (guid, path, ffmpeg_video, desired_video_codec)."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT guid, path, ffmpeg_video, desired_video_codec FROM directories WHERE active = 'active'")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logging.debug(f"✗ Error reading directories table: {e}")
        try:
            if conn:
                conn.close()
        except:
            pass
        return []


def find_video_files(directory_path, extensions=None):
    """Yield (directory, filename) tuples for video files under `directory_path`.

    `extensions` should be a list of extensions (with leading dot).
    If not provided a sensible default set will be used.
    """
    if extensions is None:
        extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts']
    # Normalize to lowercase for comparison
    lower_exts = {e.lower() for e in extensions}

    directory_path = os.path.expanduser(directory_path)
    if not os.path.isdir(directory_path):
        logging.debug(f'Not a directory: {directory_path}')
        return

    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            _, ext = os.path.splitext(file_name)
            if ext.lower() in lower_exts:
                # Yield directory path (root) and filename separately
                yield root, file_name


def is_file_unpulled_in_queue(input_file_name: str, directory_path: str, db_path: str) -> bool:
    """Check if file is already in queue."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM queue WHERE input_file_name = ? AND directory_path = ? LIMIT 1",
            (input_file_name, directory_path),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def run_ffprobe(directory_path, filename):
    """Run ffprobe for a file.

    Backwards-compatible: if `filename` is None, `path_or_dir` is treated as a full file path.
    Otherwise `path_or_dir` is a directory and `filename` is joined to it."""
    try:
        file_path = os.path.join(directory_path, filename)

        cmd = [
            'ffprobe',
            '-loglevel', 'quiet',
            '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout,color_space,color_primaries,color_transfer,side_data_list,format=nb_streams',
            '-of', 'json',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {'error': f'ffprobe failed: {result.stderr}'}
        
        probe_data = json.loads(result.stdout)
        
        # Pretty-print the ffprobe JSON output
        logging.debug(json.dumps(probe_data, indent=2))
        
        return probe_data
    
    except FileNotFoundError:
        return {'error': 'ffprobe not found. Ensure ffmpeg is installed and in PATH.'}
    except subprocess.TimeoutExpired:
        return {'error': 'ffprobe timeout (file too large or network issue)'}
    except json.JSONDecodeError:
        return {'error': 'Invalid ffprobe JSON output'}
    except Exception as e:
        return {'error': str(e)}


def check_codecs(encoding_decision, stream_info, ffmpeg_command, ffmpeg_video, desired_video_codec):
    """Check codecs in streams and build ffmpeg command."""
    streams_count = stream_info['format']['nb_streams']
    
    for i in range(0, streams_count):
        codec_type = stream_info['streams'][i]['codec_type'] 
        if codec_type == 'video':
            logging.debug('Stream ' + str(i) + ' is video')
            encoding_decision, ffmpeg_command = check_video_stream(
                encoding_decision,
                i,
                stream_info,
                ffmpeg_command,
                ffmpeg_video,
                desired_video_codec,
            )
        elif codec_type == 'audio':
            encoding_decision, ffmpeg_command = check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command)
            logging.debug('audio stream')
        elif codec_type == 'subtitle':
            encoding_decision, ffmpeg_command = check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command)
            logging.debug('subtitle stream')
        elif codec_type == 'attachment':
            encoding_decision, ffmpeg_command = check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command) 
            logging.debug('attachment stream')    
    logging.debug(encoding_decision)   
    logging.debug(ffmpeg_command)
    return encoding_decision, ffmpeg_command


def check_video_stream(encoding_decision, i, stream_info, ffmpeg_command, ffmpeg_video, desired_video_codec):
    """Checks the video stream from check_codecs to determine if the stream needs encoding."""
    codec_name = stream_info['streams'][i]['codec_name'] 

    # Check for HDR metadata and BT.2020 color space, which may require encoding to preserve HDR quality
    color_transfer = stream_info['streams'][i].get('color_transfer', '')
    color_primaries = stream_info['streams'][i].get('color_primaries', '')
    color_space = stream_info['streams'][i].get('color_space', '')
    side_data_list = stream_info['streams'][i].get('side_data_list', [])

    has_hdr_transfer = color_transfer in ('smpte2084', 'arib-std-b67')
    has_bt2020 = color_primaries == 'bt2020' or color_space in ('bt2020nc', 'bt2020c')
    has_hdr_metadata = (
        any('Mastering display' in sd.get('side_data_type', '') for sd in side_data_list)
        or any('Content light' in sd.get('side_data_type', '') for sd in side_data_list)
    )
    is_hdr = has_hdr_transfer or (has_bt2020 and has_hdr_metadata)

    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    if codec_name == desired_video_codec:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name == 'mjpeg':
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif is_hdr:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name != desired_video_codec: 
        encoding_decision = True
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + ffmpeg_video
    else:
        logging.debug('ignoring for now')
    return encoding_decision, ffmpeg_command


def check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """Checks the audio stream from check_codecs to determine if the stream needs encoding."""
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_audio_codec = 'aac'
    #if codec_name != desired_video_codec:
    #    encoding_decision = True
    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
    return encoding_decision, ffmpeg_command


def check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """Checks the subtitle stream from check_codecs to determine if the stream needs encoding."""
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_subtitle_codec = 'srt'
    #if codec_name != desired_subtitle_codec:
    #    encoding_decision = True
    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
    return encoding_decision, ffmpeg_command


def check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """Checks the attachment stream from check_codecs to determine if the stream needs encoding."""
    # This will be populated at a later date
    #desired_attachment_codec = '???'
    #if codec_name != desired_attachment_codec:
    #    encoding_decision = True
    # Note, attachments may not have a codec name if the attachment is an image
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
    return encoding_decision, ffmpeg_command


def output_file_name_fx(input_file_name, encoding_decision):
    """Generate output filename with .mkv extension if needed."""
    # Get the current extension from the filename
    name_without_ext = os.path.splitext(input_file_name)[0]
    current_ext = os.path.splitext(input_file_name)[1]
    
    # Change extension to .mkv if it's not already
    if current_ext.lower() != '.mkv':
        output_file_name = name_without_ext + '.mkv'
        encoding_decision = True
    else:
        output_file_name = input_file_name
    
    # Return just the new filename without any directory path
    return output_file_name, encoding_decision


def get_file_size_kb(directory_path, filename):
    """Get file size in KB."""
    try:
        file_path = os.path.join(directory_path, filename)
        file_size_bytes = Path(file_path).stat().st_size
        file_size_kb = int(file_size_bytes / 1024)
        return file_size_kb
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return 0
    except Exception as e:
        logging.debug(f"✗ Error getting file size: {e}")
        return 0


def write_to_queue(directory_guid, directory_path, input_file_name, output_file_name, before_file_size, ffmpeg_string, db_path):
    """Write a row into `queue` using the updated schema.

    Schema columns inserted:
      directory_guid, file_guid, directory_path, input_file_name,
      output_file_name, before_file_size, after_file_size, ffmpeg_string,
      datetime_added, datetime_pulled, datetime_encoded

    Parameters:
      - directory_guid (str)
      - directory_path (str)
      - input_file_name (str)
      - output_file_name (str)
      - before_file_size (int)
      - ffmpeg_string (str)
      - after_file_size (int|None) optional
      - db_path (str|None) optional DB path; falls back to global `db_path` variable
    """
    try:
        file_guid = str(uuid.uuid4())
        datetime_added = datetime.now().isoformat()
        after_file_size = None
        datetime_pulled = None
        datetime_encoded = None
        status = 'queued'

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO queue (directory_guid, file_guid, directory_path, input_file_name, output_file_name, before_file_size, after_file_size, ffmpeg_string, datetime_added, datetime_pulled, datetime_encoded, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                directory_guid,
                file_guid,
                directory_path,
                input_file_name,
                output_file_name,
                before_file_size,
                after_file_size,
                ffmpeg_string,
                datetime_added,
                datetime_pulled,
                datetime_encoded,
                status,
            ),
        )
        conn.commit()
        conn.close()

        logging.debug(f"✓ Wrote queue entry {file_guid} for {input_file_name}")
        return file_guid

    except Exception as e:
        logging.debug(f"✗ Error writing to queue: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return None


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
