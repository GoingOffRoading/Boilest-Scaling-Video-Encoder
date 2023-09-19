import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.close()
    except Error as e:
        print(e)


def main():
    database = r"C:\sqlite\db\ffencode_results.db"

    sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS ffencode_results (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        begin_date text,
                                        end_date text
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_projects_table)             
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()









2023-09-19 15:13:18 [2023-09-19 15:13:18,904: WARNING/ForkPoolWorker-2] {
2023-09-19 15:13:18    "config_name": "default",
2023-09-19 15:13:18    "ffmpeg_audio_codec": "opus",
2023-09-19 15:13:18    "ffmpeg_audio_string": "-c:a libopus",
2023-09-19 15:13:18    "ffmpeg_container": "MKV",
2023-09-19 15:13:18    "ffmpeg_container_extension": "mkv",
2023-09-19 15:13:18    "ffmpeg_container_string": "matroska,webm",
2023-09-19 15:13:18    "ffmpeg_encoding_string": " -c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le -c:a libopus -c:s srt",
2023-09-19 15:13:18    "ffmpeg_output_file": "A Certain Scientific Railgun - S00E02 - MMR II - Much More Railgun II.mkv",
2023-09-19 15:13:18    "ffmpeg_settings": "-hide_banner -loglevel 16 -stats",
2023-09-19 15:13:18    "ffmpeg_subtitle_format": "subrip",
2023-09-19 15:13:18    "ffmpeg_subtitle_string": "-c:s srt",
2023-09-19 15:13:18    "ffmpeg_video_codec": "av1",
2023-09-19 15:13:18    "ffmpeg_video_string": "-c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le",
2023-09-19 15:13:18    "file_name": "A Certain Scientific Railgun - S00E02 - MMR II - Much More Railgun II.mkv",
2023-09-19 15:13:18    "file_path": "/boil_watch/asd asd",
2023-09-19 15:13:18    "new_file_size": 31.441486358642578,
2023-09-19 15:13:18    "old_file_size": 34.31477642059326,
2023-09-19 15:13:18    "original_audio_codec": "aac",
2023-09-19 15:13:18    "original_container": "matroska,webm",
2023-09-19 15:13:18    "original_subtitle_format": "ass",
2023-09-19 15:13:18    "original_video_codec": "hevc",
2023-09-19 15:13:18    "output_space_difference": 2.8732900619506836,
2023-09-19 15:13:18    "production_run": "yes",
2023-09-19 15:13:18    "show_diagnostic_messages": "yes",
2023-09-19 15:13:18    "watch_folder": "/boil_watch"
2023-09-19 15:13:18 }
























