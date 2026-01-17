"""
File Prober Module
Probes video files using ffprobe and determines encoding requirements
Extracted from 02_file_prober.ipynb
"""

import sqlite3
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime


def run_ffprobe(file_path):
    """
    Run ffprobe on a video file to extract metadata
    
    Args:
        file_path: Path to the video file
        
    Returns:
        dict: Probe data or error dictionary
    """
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
        return probe_data
    
    except FileNotFoundError:
        return {'error': 'ffprobe not found. Ensure ffmpeg is installed and in PATH.'}
    except subprocess.TimeoutExpired:
        return {'error': 'ffprobe timeout (file too large or network issue)'}
    except json.JSONDecodeError:
        return {'error': 'Invalid ffprobe JSON output'}
    except Exception as e:
        return {'error': str(e)}


def check_codecs(encoding_decision, stream_info, ffmpeg_command):
    """
    Check all streams in the video file and determine encoding requirements
    
    Args:
        encoding_decision: Boolean indicating if encoding is needed
        stream_info: ffprobe output data
        ffmpeg_command: Current ffmpeg command string
        
    Returns:
        tuple: (encoding_decision, ffmpeg_command)
    """
    streams_count = stream_info['format']['nb_streams']
    
    for i in range(0, streams_count):
        codec_type = stream_info['streams'][i]['codec_type'] 
        if codec_type == 'video':
            encoding_decision, ffmpeg_command = check_video_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'audio':
            encoding_decision, ffmpeg_command = check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'subtitle':
            encoding_decision, ffmpeg_command = check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'attachment':
            encoding_decision, ffmpeg_command = check_attachment_stream(encoding_decision, i, stream_info, ffmpeg_command) 
    
    return encoding_decision, ffmpeg_command


def check_video_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """
    Check video stream codec and build appropriate ffmpeg command
    
    Args:
        encoding_decision: Boolean indicating if encoding is needed
        i: Stream index
        stream_info: ffprobe output data
        ffmpeg_command: Current ffmpeg command string
        
    Returns:
        tuple: (encoding_decision, ffmpeg_command)
    """
    codec_name = stream_info['streams'][i]['codec_name'] 
    desired_video_codec = 'av1'
    
    if codec_name == desired_video_codec:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name == 'mjpeg':
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name != desired_video_codec: 
        encoding_decision = True
        svt_av1_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + svt_av1_string
    
    return encoding_decision, ffmpeg_command


def check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """
    Check audio stream codec and build appropriate ffmpeg command
    
    Args:
        encoding_decision: Boolean indicating if encoding is needed
        i: Stream index
        stream_info: ffprobe output data
        ffmpeg_command: Current ffmpeg command string
        
    Returns:
        tuple: (encoding_decision, ffmpeg_command)
    """
    codec_name = stream_info['streams'][i]['codec_name']
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
    return encoding_decision, ffmpeg_command


def check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """
    Check subtitle stream codec and build appropriate ffmpeg command
    
    Args:
        encoding_decision: Boolean indicating if encoding is needed
        i: Stream index
        stream_info: ffprobe output data
        ffmpeg_command: Current ffmpeg command string
        
    Returns:
        tuple: (encoding_decision, ffmpeg_command)
    """
    codec_name = stream_info['streams'][i]['codec_name']
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
    return encoding_decision, ffmpeg_command


def check_attachment_stream(encoding_decision, i, stream_info, ffmpeg_command):
    """
    Check attachment stream and build appropriate ffmpeg command
    
    Args:
        encoding_decision: Boolean indicating if encoding is needed
        i: Stream index
        stream_info: ffprobe output data
        ffmpeg_command: Current ffmpeg command string
        
    Returns:
        tuple: (encoding_decision, ffmpeg_command)
    """
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
    return encoding_decision, ffmpeg_command


def output_file_name(file_path, needs_encoding):
    """
    Determine output filename, changing extension to .mkv if needed
    
    Args:
        file_path: Path to the input file
        needs_encoding: Boolean indicating if encoding is needed
        
    Returns:
        tuple: (new_filename, needs_encoding)
    """
    # Get the filename and current extension
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    current_ext = os.path.splitext(filename)[1]
    
    # Change extension to .mkv if it's not already
    if current_ext.lower() != '.mkv':
        new_filename = name_without_ext + '.mkv'
        needs_encoding = True
    else:
        new_filename = filename
    
    # Return just the new filename without any directory path
    return new_filename, needs_encoding


def get_file_size_kb(file_path):
    """
    Get file size in kilobytes
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: File size in KB, or 0 if error
    """
    try:
        file_size_bytes = Path(file_path).stat().st_size
        file_size_kb = int(file_size_bytes / 1024)
        return file_size_kb
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return 0
    except Exception as e:
        print(f"✗ Error getting file size: {e}")
        return 0


def write_to_encode(file_path, guid, db_path):
    """
    Probe a file and write encoding information to the encode table
    
    Args:
        file_path: Path to the video file
        guid: GUID for the file
        db_path: Path to the database
        
    Returns:
        dict: Encode record data or None if error
    """
    try:
        # Use provided guid
        directory_path = os.path.dirname(file_path)
        input_file_name = os.path.basename(file_path)

        # Get file size in KB
        before_file_size = get_file_size_kb(file_path)

        # Probe file and determine encoding via check_codecs
        probe_data = run_ffprobe(file_path)
        ffmpeg_command = ""
        needs_encoding = False

        if isinstance(probe_data, dict) and 'error' in probe_data:
            print(f"Error probing file: {probe_data['error']}")
            # Keep defaults: needs_encoding=False, ffmpeg_command=""
        else:
            needs_encoding, ffmpeg_command = check_codecs(needs_encoding, probe_data, ffmpeg_command)

        # Only populate output_file and ffmpeg_string if needs_encoding is True
        if needs_encoding:
            output_file, _ = output_file_name(file_path, needs_encoding)
            ffmpeg_string = ffmpeg_command
        else:
            output_file = None
            ffmpeg_string = None

        # Get current datetime
        date_added = datetime.now().isoformat()

        # Convert decision to string
        decision = str(needs_encoding)

        # Write to database
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO encode (guid, directory_path, input_file_name, output_file_name, 
                               before_file_size, decision, ffmpeg_string, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (guid, directory_path, input_file_name, output_file, before_file_size, decision, ffmpeg_string, date_added))

        conn.commit()
        conn.close()

        print(f"✓ Successfully wrote encode record for {input_file_name}")

        return {
            'guid': guid,
            'directory_path': directory_path,
            'input_file_name': input_file_name,
            'output_file_name': output_file,
            'before_file_size': before_file_size,
            'decision': decision,
            'ffmpeg_string': ffmpeg_string,
            'date_added': date_added
        }

    except Exception as e:
        print(f"✗ Error writing to encode table: {e}")
        return None


def enqueue_all_files_for_encoding(db_path):
    """
    Process all files in the database that need encoding analysis
    
    Args:
        db_path: Path to the database
        
    Returns:
        list: List of results for each file processed
    """
    results = []
    skip_guids = set()
    processed = 0

    while True:
        conn = None
        row = None
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()

            if skip_guids:
                placeholders = ",".join(["?"] * len(skip_guids))
                cur.execute(
                    f"""
                    SELECT f.guid, f.file_path
                    FROM files f
                    LEFT JOIN encode e ON e.guid = f.guid
                    LEFT JOIN encoded enc ON enc.guid = f.guid
                    WHERE e.guid IS NULL AND enc.guid IS NULL AND f.guid NOT IN ({placeholders})
                    LIMIT 1
                    """,
                    tuple(skip_guids),
                )
            else:
                cur.execute(
                    """
                    SELECT f.guid, f.file_path
                    FROM files f
                    LEFT JOIN encode e ON e.guid = f.guid
                    LEFT JOIN encoded enc ON enc.guid = f.guid
                    WHERE e.guid IS NULL AND enc.guid IS NULL
                    LIMIT 1
                    """
                )

            row = cur.fetchone()
        except Exception as e:
            print(f"✗ Error querying next file: {e}")
            break
        finally:
            if conn:
                conn.close()

        if not row:
            print(f"✓ No more files requiring encode. Processed {processed} file(s).")
            break

        guid, file_path = row

        if not file_path:
            print(f"✗ Missing file path for guid {guid}")
            skip_guids.add(guid)
            results.append({"guid": guid, "file_path": file_path, "error": "missing file_path"})
            continue

        if not Path(file_path).exists():
            print(f"✗ File not found on disk for guid {guid}: {file_path}")
            skip_guids.add(guid)
            results.append({"guid": guid, "file_path": file_path, "error": "file not found on disk"})
            continue

        result = write_to_encode(file_path, guid, db_path)
        results.append({"guid": guid, "file_path": file_path, "write_result": result})
        processed += 1

    print(f"✓ Attempted encode writes for {len(results)} file(s)")
    return results
