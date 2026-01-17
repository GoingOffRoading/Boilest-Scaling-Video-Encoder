"""
File Scanner Module
Scans directories for video files and adds them to the database
Extracted from 01_search_files.ipynb
"""

import sqlite3
import os
import uuid
from pathlib import Path


def write_file_to_database(db_path, directory_guid, file_path, file_name):
    """
    Write a file record to the database
    
    Args:
        db_path: Path to the database file
        directory_guid: GUID of the parent directory
        file_path: Full path to the file
        file_name: Name of the file
        
    Returns:
        dict: Result containing success status and guid or error message
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # Check if file_path already exists
        cur.execute('SELECT guid FROM files WHERE file_path = ?', (file_path,))
        existing = cur.fetchone()
        
        if existing:
            return {
                'success': False,
                'error': 'File path already exists',
                'existing_guid': existing[0]
            }
        
        # File path doesn't exist, insert new record
        guid = str(uuid.uuid4())
        cur.execute(
            'INSERT INTO files (guid, directory_guid, file_path, file_name) VALUES (?, ?, ?, ?)',
            (guid, directory_guid, file_path, file_name)
        )
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'guid': guid
        }
    
    except sqlite3.IntegrityError as e:
        return {'success': False, 'error': f'Database integrity error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}


def scan_directories_and_enqueue(db_path):
    """
    Scan all directories in the database for video files
    
    Args:
        db_path: Path to the database file
        
    Returns:
        dict: Summary of scan results including files found, written, skipped, and errors
    """
    extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts']

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    try:
        # Get all directories with their GUIDs
        cur.execute("SELECT guid, path FROM directories")
        directories = cur.fetchall()
        print(f'Directories found: {directories}')
    except Exception as e:
        print('Error reading directories table:', e)
        conn.close()
        return {'error': str(e)}
    finally:
        conn.close()

    files_found = 0
    files_written = 0
    files_skipped = 0
    errors = []

    for directory_guid, path in directories:
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            print(f'Directory not found: {path}')
            errors.append(f'Directory not found: {path}')
            continue
        
        # Walk directory and write each matching file to database
        for root, dirs, files in os.walk(path):
            for file in files:
                for ext in extensions:
                    if file.lower().endswith(ext.lower()):
                        files_found += 1
                        file_path = os.path.join(root, file)
                        
                        # Write file to database
                        result = write_file_to_database(db_path, directory_guid, file_path, file)
                        
                        if result['success']:
                            print(f'✓ Added: {file_path} (guid={result["guid"]})')
                            files_written += 1
                        else:
                            if 'already exists' in result.get('error', ''):
                                print(f'⊘ Skipped (exists): {file_path}')
                                files_skipped += 1
                            else:
                                print(f'✗ Error: {file_path} - {result.get("error")}')
                                errors.append(f'Failed to write {file_path}: {result.get("error")}')
                        
                        if (files_written + files_skipped) % 100 == 0:
                            print(f'Progress: {files_written} written, {files_skipped} skipped...')
                        
                        break  # Only match one extension per file
    
    summary = {
        'files_found': files_found,
        'files_written': files_written,
        'files_skipped': files_skipped,
        'errors': errors
    }
    
    print("-" * 80)
    print(f"Scan complete: {files_found} files found, {files_written} written, {files_skipped} skipped")
    if errors:
        print(f"Errors: {len(errors)}")
    return summary
