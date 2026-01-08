import sqlite3
import subprocess
import json
from pathlib import Path

def get_unprocessed_files(db_path='boilest.db'):
    """
    Get all files that exist in the files table but don't have an encode record yet.
    
    Args:
        db_path (str): Path to the database file
    
    Returns:
        list: List of unprocessed files with guid, file_path, file_name
    """
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # LEFT ANTI JOIN: files that have no corresponding encode record
        cur.execute("""
            SELECT f.guid, f.file_path, f.file_name, f.directory_guid
            FROM files f
            LEFT JOIN encode e ON f.guid = e.guid
            WHERE e.guid IS NULL
        """)
        
        unprocessed = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return unprocessed
    
    except Exception as e:
        print(f"✗ Error querying database: {e}")
        return []


def run_ffprobe(file_path):
    """
    Run ffprobe on a file and return media information.
    
    Args:
        file_path (str): Full path to the media file
    
    Returns:
        dict: ffprobe output (streams, format info) or error details
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'format=duration,size,bit_rate:stream=width,height,codec_type,codec_name,r_frame_rate',
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


def probe_unprocessed_files(db_path='boilest.db'):
    """
    Get all unprocessed files and run ffprobe on each.
    
    Args:
        db_path (str): Path to the database file
    
    Returns:
        dict: Summary with processed files and results
    """
    unprocessed = get_unprocessed_files(db_path)
    
    if not unprocessed:
        print("✓ No unprocessed files found. All files have encode records.")
        return {'total': 0, 'results': []}
    
    print(f"Found {len(unprocessed)} unprocessed files")
    print("=" * 80)
    
    results = []
    
    for idx, file_info in enumerate(unprocessed, 1):
        file_path = file_info['file_path']
        file_name = file_info['file_name']
        guid = file_info['guid']
        
        print(f"\n[{idx}/{len(unprocessed)}] Probing: {file_name}")
        print(f"  Path: {file_path}")
        
        # Check if file exists
        if not Path(file_path).exists():
            print(f"  ✗ File not found on disk")
            results.append({
                'guid': guid,
                'file_name': file_name,
                'file_path': file_path,
                'error': 'File not found on disk'
            })
            continue
        
        # Run ffprobe
        probe_result = run_ffprobe(file_path)
        
        if 'error' in probe_result:
            print(f"  ✗ Error: {probe_result['error']}")
            results.append({
                'guid': guid,
                'file_name': file_name,
                'file_path': file_path,
                'error': probe_result['error']
            })
        else:
            # Extract relevant info
            format_info = probe_result.get('format', {})
            streams = probe_result.get('streams', [])
            
            duration = format_info.get('duration', 'N/A')
            size = format_info.get('size', 'N/A')
            bit_rate = format_info.get('bit_rate', 'N/A')
            
            video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
            
            if video_stream:
                width = video_stream.get('width', 'N/A')
                height = video_stream.get('height', 'N/A')
                codec = video_stream.get('codec_name', 'N/A')
                frame_rate = video_stream.get('r_frame_rate', 'N/A')
                
                print(f"  ✓ Duration: {duration}s")
                print(f"  ✓ Size: {size} bytes")
                print(f"  ✓ Resolution: {width}x{height}")
                print(f"  ✓ Codec: {codec}")
                print(f"  ✓ Frame rate: {frame_rate}")
                
                results.append({
                    'guid': guid,
                    'file_name': file_name,
                    'file_path': file_path,
                    'duration': duration,
                    'size': size,
                    'bit_rate': bit_rate,
                    'width': width,
                    'height': height,
                    'codec': codec,
                    'frame_rate': frame_rate,
                    'full_probe': probe_result
                })
            else:
                print(f"  ⚠ No video stream found")
                results.append({
                    'guid': guid,
                    'file_name': file_name,
                    'file_path': file_path,
                    'warning': 'No video stream found',
                    'full_probe': probe_result
                })
    
    print("\n" + "=" * 80)
    print(f"✓ Probed {len(results)} files")
    
    return {
        'total': len(unprocessed),
        'probed': len(results),
        'results': results
    }
