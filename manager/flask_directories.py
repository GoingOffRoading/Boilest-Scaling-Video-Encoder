import sqlite3
import logging
from datetime import datetime
from uuid import uuid4
from db_path import get_db_path

__all__ = ["create_directory_logic", "update_directory_logic", "delete_directory_logic"]


_ALLOWED_FIELDS = {
    "path",
    "ffmpeg_video",
    "ffmpeg_audio",
    "ffmpeg_subtitle",
    "desired_video_codec",
    "desired_audio_codec",
    "desired_subtitle_codec",
}


def _filter_fields(data):
    return {key: value for key, value in data.items() if key in _ALLOWED_FIELDS}


def create_directory_logic(data):
    """
    Create a new directory record.

    Returns:
        tuple: (response_dict, status_code)
    """
    path = (data or {}).get("path")
    if not path:
        return {
            "success": False,
            "error": "Missing required field: path"
        }, 400

    fields = _filter_fields(data or {})
    guid = str(uuid4())
    added_at = datetime.now().isoformat()

    columns = ["guid", "path", "added_at"] + list(fields.keys())
    values = [guid, path, added_at] + [fields[key] for key in fields.keys()]
    placeholders = ", ".join(["?"] * len(values))

    logging.info("[REQUEST] POST /api/directories")

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        insert_sql = f"INSERT INTO directories ({', '.join(columns)}) VALUES ({placeholders})"
        cur.execute(insert_sql, values)
        conn.commit()
        conn.close()

        logging.info(f"[SUCCESS] Created directory: {guid}")
        return {
            "success": True,
            "data": {
                "guid": guid,
                "path": path,
                "added_at": added_at,
                **fields
            }
        }, 201

    except Exception as e:
        logging.error(f"[ERROR] Failed to create directory: {e}")
        return {
            "success": False,
            "error": str(e)
        }, 500


def update_directory_logic(guid, data):
    """
    Update an existing directory record.

    Returns:
        tuple: (response_dict, status_code)
    """
    if not guid:
        return {
            "success": False,
            "error": "Missing required parameter: guid"
        }, 400

    fields = _filter_fields(data or {})
    if not fields:
        return {
            "success": False,
            "error": "No updatable fields provided"
        }, 400

    set_clause = ", ".join([f"{key} = ?" for key in fields.keys()])
    values = list(fields.values()) + [guid]

    logging.info("[REQUEST] PATCH /api/directories/<guid>")

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        update_sql = f"UPDATE directories SET {set_clause} WHERE guid = ?"
        cur.execute(update_sql, values)
        conn.commit()
        updated_count = cur.rowcount
        conn.close()

        if updated_count == 0:
            return {
                "success": False,
                "error": "Directory not found"
            }, 404

        logging.info(f"[SUCCESS] Updated directory: {guid}")
        return {
            "success": True,
            "updated_count": updated_count
        }, 200

    except Exception as e:
        logging.error(f"[ERROR] Failed to update directory {guid}: {e}")
        return {
            "success": False,
            "error": str(e)
        }, 500


def delete_directory_logic(guid):
    """
    Soft-delete a directory record by setting active to 'false'.

    Returns:
        tuple: (response_dict, status_code)
    """
    if not guid:
        return {
            "success": False,
            "error": "Missing required parameter: guid"
        }, 400

    logging.info("[REQUEST] DELETE /api/directories/<guid>")

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("UPDATE directories SET active = 'inactive' WHERE guid = ?", (guid,))
        conn.commit()
        updated_count = cur.rowcount
        conn.close()

        if updated_count == 0:
            return {
                "success": False,
                "error": "Directory not found"
            }, 404

        logging.info(f"[SUCCESS] Deactivated directory: {guid}")
        return {
            "success": True,
            "updated_count": updated_count
        }, 200

    except Exception as e:
        logging.error(f"[ERROR] Failed to deactivate directory {guid}: {e}")
        return {
            "success": False,
            "error": str(e)
        }, 500
