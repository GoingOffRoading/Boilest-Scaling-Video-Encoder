import os
import subprocess
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


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
