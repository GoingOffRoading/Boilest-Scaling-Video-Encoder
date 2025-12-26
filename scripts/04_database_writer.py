import logging
import sqlite3
from datetime import datetime
import os

# create logger
logger = logging.getLogger('boilest_logs')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

def write_results(file_located_data):
    unique_identifier = file_located_data['file'] + str(datetime.now().microsecond)
    file_name = file_located_data['file']
    file_path = file_located_data['file_path']
    config_name = 'placeholder'
    new_file_size = file_located_data['new_file_size']
    old_file_size = file_located_data['old_file_size']
    new_file_size_difference = old_file_size - new_file_size
    watch_folder = file_located_data['directory']
    ffmpeg_encoding_string = file_located_data['ffmpeg_command']

    if len(ffmpeg_encoding_string) > 999:
        # the varchar for ffmpeg_encoding_string is 999 characters.  This is to keep the db write from failing at 1000 characters
        ffmpeg_encoding_string = ffmpeg_encoding_string[:999]

    logger.info('Writing results')
    insert_record(unique_identifier, file_name, file_path, config_name, new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string)
    logger.info('Writing results complete')

def insert_record(unique_identifier, file_name, file_path, config_name, new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string):
    db_path = '/app/data/boilest.db'
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to SQLite database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Create table if it doesn't exist
        create_table_query = """
            CREATE TABLE IF NOT EXISTS ffmpeghistory (
                unique_identifier TEXT PRIMARY KEY,
                recorded_date TEXT,
                file_name TEXT,
                file_path TEXT,
                config_name TEXT,
                new_file_size INTEGER,
                new_file_size_difference INTEGER,
                old_file_size INTEGER,
                watch_folder TEXT,
                ffmpeg_encoding_string TEXT
            )
        """
        cursor.execute(create_table_query)
        
        recorded_date = datetime.now().isoformat()  # ISO format for SQLite
        
        insert_query = """
            INSERT INTO ffmpeghistory (
                unique_identifier, recorded_date, file_name, file_path, config_name,
                new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        record = (
            unique_identifier, recorded_date, file_name, file_path, config_name,
            new_file_size, new_file_size_difference, old_file_size, watch_folder, ffmpeg_encoding_string
        )
        
        cursor.execute(insert_query, record)
        connection.commit()
        logger.debug("Record inserted successfully into SQLite database")
        
    except sqlite3.Error as e:
        logger.error(f"Error while working with SQLite: {e}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            logger.debug("SQLite connection is closed")