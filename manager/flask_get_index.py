import sqlite3
import logging
from datetime import datetime
from db_path import get_db_path

__all__ = ["get_index_data"]


def _format_kb_size(kb_value):
    if kb_value is None:
        return None, None

    size_kb = float(kb_value)
    abs_size_kb = abs(size_kb)

    if abs_size_kb >= (1024 * 1024 * 1024):
        return round(size_kb / (1024 * 1024 * 1024), 2), "TB"
    if abs_size_kb >= (1024 * 1024):
        return round(size_kb / (1024 * 1024), 2), "GB"
    return round(size_kb / 1024, 2), "MB"


def _format_minutes_duration(total_minutes):
    if total_minutes is None:
        return None, None

    minutes = float(total_minutes)
    abs_minutes = abs(minutes)

    minutes_per_hour = 60
    minutes_per_day = 24 * minutes_per_hour
    minutes_per_week = 7 * minutes_per_day
    minutes_per_month = 30 * minutes_per_day
    minutes_per_year = 365 * minutes_per_day

    if abs_minutes >= minutes_per_year:
        return round(minutes / minutes_per_year, 2), "years"
    if abs_minutes >= minutes_per_month:
        return round(minutes / minutes_per_month, 2), "months"
    if abs_minutes >= minutes_per_week:
        return round(minutes / minutes_per_week, 2), "weeks"
    if abs_minutes >= minutes_per_day:
        return round(minutes / minutes_per_day, 2), "days"
    return round(minutes / minutes_per_hour, 2), "hours"


def get_index_data():
    """
    Get data for the index page
    
    Returns:
        dict: Dictionary containing metrics, queued items, encoding items, and recently encoded items
    """
    logging.info("[UI] Fetching index page data")
    
    queued_count = 0
    processing_count = 0
    encoded_count = 0
    space_saved_gb = 0.0
    space_saved_value = 0.0
    space_saved_unit = "MB"
    total_processing_minutes = 0.0
    total_processing_value = 0.0
    total_processing_unit = "hours"
    queued_items = []
    encoding_items = []
    encoded_items = []
    failed_items = []
    directories_items = []
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        

        # =====================================================
        #                   Main Page Metrics
        # =====================================================

        # Get queued count
        cur.execute("SELECT COUNT(*) FROM queue WHERE status='queued'")
        queued_count = cur.fetchone()[0]
        logging.debug(f"[UI] Queued count: {queued_count}")
        
        # Get active workers count (distinct workers with pulls in last 24 hours)
        cur.execute("SELECT COUNT(DISTINCT worker) FROM queue WHERE datetime_pulled > datetime('now', '-24 hours')")
        processing_count = cur.fetchone()[0]
        logging.debug(f"[UI] Active workers count: {processing_count}")
        
        # Get encoded count
        cur.execute("SELECT COUNT(*) FROM queue WHERE status='encoded'")
        encoded_count = cur.fetchone()[0]
        logging.debug(f"[UI] Encoded count: {encoded_count}")
        
        # Get space saved (in KB, convert to GB)
        cur.execute("SELECT SUM(before_file_size) - SUM(after_file_size) as space_saved FROM queue WHERE status='encoded'")
        space_saved_result = cur.fetchone()
        if space_saved_result and space_saved_result['space_saved'] is not None:
            space_saved_kb = space_saved_result['space_saved']
            space_saved_gb = round(space_saved_kb / (1024 * 1024), 2)
            space_saved_value, space_saved_unit = _format_kb_size(space_saved_kb)
        else:
            space_saved_value, space_saved_unit = 0.0, "MB"
        logging.debug(f"[UI] Space saved: {space_saved_gb} GB")
        
        # Calculate total processing time across all encoded records
        cur.execute("""
            SELECT SUM((julianday(datetime_encoded) - julianday(datetime_pulled)) * 24 * 60) AS total_minutes
            FROM queue
            WHERE status = 'encoded'
              AND datetime_pulled IS NOT NULL
              AND datetime_encoded IS NOT NULL
        """)
        total_minutes_result = cur.fetchone()
        if total_minutes_result and total_minutes_result['total_minutes'] is not None:
            total_processing_minutes = float(total_minutes_result['total_minutes'])
        else:
            total_processing_minutes = 0.0
        total_processing_value, total_processing_unit = _format_minutes_duration(total_processing_minutes)
        logging.debug(f"[UI] Total processing time: {total_processing_minutes} minutes")

    
        # =====================================================
        #                   Queued Files Table
        # =====================================================

        # Get queued items
        cur.execute("""
            SELECT 
                ROWID,
                file_guid,
                directory_path,
                input_file_name,
                before_file_size,
                ffmpeg_string,
                datetime_added
            FROM queue 
            WHERE status = 'queued'
            ORDER BY ROWID DESC
            LIMIT 100
        """)
        raw_items = cur.fetchall()
        queued_items = []
        for row in raw_items:
            item = {
                'ROWID': row['ROWID'],
                'Filename': row['input_file_name'],
                'Path': row['directory_path'],
                'SizeMB': round(row['before_file_size'] / 1024, 2) if row['before_file_size'] is not None else None,
                'ffmpeg_string': row['ffmpeg_string'],
                'Added': None
            }
            dt = row['datetime_added']
            if dt:
                try:
                    item['Added'] = datetime.fromisoformat(dt).strftime('%Y-%m-%d %H-%M')
                except Exception:
                    item['Added'] = dt
            queued_items.append(item)
        logging.debug(f"[UI] Retrieved {len(queued_items)} queued items")


        # =====================================================
        #                   Currently Encoding Table
        # =====================================================
        
        # Get currently encoding items sorted by datetime_pulled ascending
        cur.execute("""
            SELECT 
                ROWID,
                file_guid,
                directory_path,
                input_file_name,
                before_file_size,
                ffmpeg_string,
                datetime_pulled,
                worker
            FROM queue 
            WHERE status = 'pulled'
            ORDER BY datetime_pulled ASC
            LIMIT 100
        """)
        raw_encoding = cur.fetchall()
        encoding_items = []
        for row in raw_encoding:
            item = {
                'ROWID': row['ROWID'],
                'worker': row['worker'],
                'input_file_name': row['input_file_name'],
                'directory_path': row['directory_path'],
                'SizeMB': round(row['before_file_size'] / 1024, 2) if row['before_file_size'] is not None else None,
                'ffmpeg_string': row['ffmpeg_string'],
                'Pulled': None
            }
            dt_pulled = row['datetime_pulled']
            if dt_pulled:
                try:
                    item['Pulled'] = datetime.fromisoformat(dt_pulled).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    item['Pulled'] = dt_pulled
            encoding_items.append(item)
        logging.debug(f"[UI] Retrieved {len(encoding_items)} currently encoding items")

        # =====================================================
        #                   Recently Encoded Table
        # =====================================================
        
        # Get recently encoded items sorted by datetime_encoded descending
        cur.execute("""
            SELECT 
                ROWID,
                output_file_name,
                directory_path,
                before_file_size - after_file_size as space_saved,
                datetime_pulled,
                datetime_encoded,
                worker
            FROM queue 
            WHERE status = 'encoded'
            ORDER BY datetime_encoded DESC
            LIMIT 100
        """)
        raw_encoded = cur.fetchall()
        encoded_items = []
        for row in raw_encoded:
            item = {
                'ROWID': row['ROWID'],
                'worker': row['worker'],
                'output_file_name': row['output_file_name'],
                'directory_path': row['directory_path'],
                'space_saved': row['before_file_size - after_file_size'] if 'before_file_size - after_file_size' in row.keys() else row['space_saved'],
                'datetime_pulled': row['datetime_pulled'],
                'datetime_encoded': row['datetime_encoded'],
                'duration_minutes': None,
                'space_saved_mb': None,
                'Completed': None
            }
            dp = item.get('datetime_pulled')
            de = item.get('datetime_encoded')
            if dp and de:
                try:
                    dt_pulled = datetime.fromisoformat(dp)
                    dt_encoded = datetime.fromisoformat(de)
                    delta = dt_encoded - dt_pulled
                    item['duration_minutes'] = round(delta.total_seconds() / 60, 2)
                except Exception:
                    item['duration_minutes'] = None
            # Convert space_saved from KB to MB for display
            try:
                ss = item.get('space_saved')
                if ss is not None:
                    item['space_saved_mb'] = round(ss / 1024, 2)
                else:
                    item['space_saved_mb'] = None
            except Exception:
                item['space_saved_mb'] = None
            # Format datetime_encoded as YYYY-MM-DD HH:MM
            if de:
                try:
                    item['Completed'] = datetime.fromisoformat(de).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    item['Completed'] = de
            else:
                item['Completed'] = None
            encoded_items.append(item)
        logging.debug(f"[UI] Retrieved {len(encoded_items)} recently encoded items")
        
        # =====================================================
        #                   Recently Failed Table
        # =====================================================

        # Get recently failed items (include any non-active statuses and explicitly include 'stopped')
        cur.execute("""
            SELECT 
                ROWID,
                input_file_name,
                directory_path,
                datetime_pulled,
                status,
                worker
            FROM queue 
            WHERE status NOT IN ('queued', 'pulled', 'encoded') OR status = 'stopped'
            ORDER BY datetime_pulled DESC
            LIMIT 100
        """)
        raw_failed = cur.fetchall()
        failed_items = []
        for row in raw_failed:
            item = {
                'ROWID': row['ROWID'],
                'worker': row['worker'],
                'input_file_name': row['input_file_name'],
                'directory_path': row['directory_path'],
                'datetime_pulled': row['datetime_pulled'],
                'status': row['status']
            }
            failed_items.append(item)
        logging.debug(f"[UI] Retrieved {len(failed_items)} recently failed items")


        # =====================================================
        #                   Directories Table
        # =====================================================
        
        # Get all active directories
        cur.execute("SELECT * FROM directories WHERE active = 'active'")
        directories_items = [dict(row) for row in cur.fetchall()]
        logging.debug(f"[UI] Retrieved {len(directories_items)} directories")
        
        conn.close()
    except Exception as e:
        logging.error(f"[ERROR] Failed to get index data: {e}")
    
    return {
        'queued_count': queued_count,
        'processing_count': processing_count,
        'encoded_count': encoded_count,
        'space_saved_gb': space_saved_gb,
        'space_saved_value': space_saved_value,
        'space_saved_unit': space_saved_unit,
        'total_processing_minutes': round(total_processing_minutes, 2),
        'total_processing_value': total_processing_value,
        'total_processing_unit': total_processing_unit,
        'queued_items': queued_items,
        'encoding_items': encoding_items,
        'encoded_items': encoded_items,
        'failed_items': failed_items,
        'directories_items': directories_items
    }
