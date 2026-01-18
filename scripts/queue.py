from datetime import datetime
import sqlite3
import os
import uuid
import subprocess
import json
import logging
from scripts.db_path import get_db_path
from scripts.get_file_size_kb import get_file_size_kb

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

logging.debug("Libraries imported successfully")

db_path = get_db_path()

# =============================================================================
# Get Directories
# =============================================================================
# Todo:
# - [ ] Figure out better connection open/close logic 

def get_all_directories(db_path):
    """Return all rows from the `directories` table as a list of (guid, path)."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT guid, path FROM directories")
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


# =============================================================================
# Directory Scanner
# =============================================================================

# Note: `write_file_to_database` removed from this cell. Use central database utilities instead.

def scan_directories_and_enqueue(directory_path, directory_guid=None, extensions=None):
    if extensions is None:
        extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts']
    directory_path = os.path.expanduser(directory_path)
    if not os.path.isdir(directory_path):
        logging.debug(f'Directory not found: {directory_path}')
        return
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            for ext in extensions:
                if file.lower().endswith(ext.lower()):
                    file_path = os.path.join(root, file)
                    yield {
                        'directory_guid': directory_guid,
                        'root': root,
                        'file': file,
                        'file_path': file_path
                    }
                    break  # Only match one extension per file


# =============================================================================
# FFProbe Function
# =============================================================================
# Todo:
# - [ ] Research expanding the entries on the ffprobe string for HDR and other criteria

def run_ffprobe(file_path):
    try:
        cmd = [
            'ffprobe',
            '-loglevel', 'quiet',
            '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout,format=nb_streams',  
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


# =============================================================================
# Check Codecs
# =============================================================================
# Loops through the streams in stream_info from requires_encoding, then calls 
# functions to determine if the steam needs encoding based on stream type conditions 
#
# Todo:
# - [x] Copy over the stream looping function from Boilest v1.0
# - [ ] Research SVT-AV1 best practices for various media types
# - [ ] Store SVT-AV1 best practice presets in the DB
# - [ ] Call best-practive presets in check_video_stream
# - [ ] Determine what audio codec to go with
# - [ ] Determine what the compromises will be if ASS subtitles are re-encoded as SubRip
# - [ ] Determine if there are consequences for deleting attachments 

def check_codecs(encoding_decision,stream_info, ffmpeg_command):
    streams_count = stream_info['format']['nb_streams']
    
    for i in range (0,streams_count):
        codec_type = stream_info['streams'][i]['codec_type'] 
        if codec_type == 'video':
            logging.debug('Stream ' + str(i) + ' is video')
            encoding_decision, ffmpeg_command = check_video_stream(encoding_decision, i, stream_info, ffmpeg_command)
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

def check_video_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the video stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    desired_video_codec = 'av1'
    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    if codec_name == desired_video_codec:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name == 'mjpeg':
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name != desired_video_codec: 
        encoding_decision = True
        svt_av1_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + svt_av1_string
    else:
        logging.debug('ignoring for now')
    return encoding_decision, ffmpeg_command


def check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the audio stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_audio_codec = 'aac'
    #if codec_name != desired_video_codec:
    #    encoding_decision = True
    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
    return encoding_decision, ffmpeg_command


def check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the subtitle stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_subtitle_codec = 'srt'
    #if codec_name != desired_subtitle_codec:
    #    encoding_decision = True
    logging.debug('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
    return encoding_decision, ffmpeg_command


def check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the attachment stream from check_codecs to determine if the stream needs encoding
    # This will be populated at a later date
    #desired_attachment_codec = '???'
    #if codec_name != desired_attachment_codec:
    #    encoding_decision = True
    # Note, attachments may not have a codec name if the attachment is an image
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
    return encoding_decision, ffmpeg_command


# =============================================================================
# File Output Naming Function
# =============================================================================

def output_file_name(file_path, encoding_decision):
    # Get the filename and current extension
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    current_ext = os.path.splitext(filename)[1]
    
    # Change extension to .mkv if it's not already
    if current_ext.lower() != '.mkv':
        new_filename = name_without_ext + '.mkv'
        encoding_decision = True
    else:
        new_filename = filename
    
    # Return just the new filename without any directory path
    return new_filename, encoding_decision


# =============================================================================
# Get File Size Function
# =============================================================================
# Moved to scripts.get_file_size_kb.get_file_size_kb and imported above.


# =============================================================================
# Write to Queue Function
# =============================================================================

def write_to_queue(directory_guid, file_path, output_file_name, before_file_size, ffmpeg_string):
    """Write an entry into the `queue` table in boilest.db."""
    try:
        guid = str(uuid.uuid4())
        date_added = datetime.now().isoformat()
        input_file_name = os.path.basename(file_path)

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Resolve directory path from provided directory GUID if possible
        directory_path = None
        try:
            cur.execute("SELECT path FROM directories WHERE guid = ?", (directory_guid,))
            row = cur.fetchone()
            if row:
                directory_path = row[0]
        except Exception:
            directory_path = None

        # Fallback to dirname of file_path if directory_path not found
        if not directory_path:
            directory_path = os.path.dirname(file_path)

        cur.execute("INSERT INTO queue (guid, directory_guid, file_path, output_file_name, before_file_size, ffmpeg_string, date_added) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (guid, directory_guid, file_path, output_file_name, before_file_size, ffmpeg_string, date_added))
        conn.commit()
        conn.close()
        logging.debug(f"✓ Wrote queue entry {guid} for {input_file_name}")
        return guid
    except Exception as e:
        logging.debug(f"✗ Error writing to queue: {e}")
        try:
            conn.close()
        except:
            pass
        return None


# =============================================================================
# Pulling it all together
# =============================================================================

def write_to_db (file_path, directory_guid):
    logging.debug(file_path)
    default_encoding_decision = False
    logging.debug(default_encoding_decision)
    file_size = get_file_size_kb(file_path)
    logging.debug(file_size)
    new_filename_value, new_encoding_decision = output_file_name(file_path, default_encoding_decision)
    logging.debug(new_filename_value)
    logging.debug(new_encoding_decision)
    stream_info = run_ffprobe(file_path)
    ffmpeg_command = ''
    final_encoding_decision, new_ffmpeg_command = check_codecs(new_encoding_decision, stream_info, ffmpeg_command)
    logging.debug(final_encoding_decision)
    logging.debug(new_ffmpeg_command)
    if final_encoding_decision == True:
        logging.debug('Queue file for encoding')
        write_to_queue(directory_guid, file_path, new_filename_value, file_size, new_ffmpeg_command)
    else:
        logging.debug('Do not queue file for encoding')

#write_to_db(file_path, None)


def scan_db_directories_and_write(db_path=None, extensions=None):
    """Scan all directories stored in the `directories` table and for each file found
    call `write_to_db` with the file path. Returns the number of files processed.
    """
    rows = get_all_directories(db_path)
    if not rows:
        logging.debug('No directories found in DB.')
        return 0
    total = 0
    for guid, path in rows:
        logging.debug(f'Scanning directory {path} (guid={guid})')
        for item in scan_directories_and_enqueue(path, directory_guid=guid, extensions=extensions):
            # Each yielded item is expected to be a dict with a 'file_path' key
            file_path = item.get('file_path') if isinstance(item, dict) else None
            if not file_path:
                logging.debug(f'✗ Skipping item without file_path: {item}')
                continue
            try:
                write_to_db(file_path,guid)
                total += 1
            except Exception as e:
                logging.debug(f'✗ Error processing {file_path}: {e}')
    logging.debug(f'Done. Total files processed: {total}')
    return total


if __name__ == '__main__':
    # Example usage (uncomment to run):
    scan_db_directories_and_write(db_path)
