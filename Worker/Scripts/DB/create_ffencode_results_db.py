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

    sql_create_results_table = """ CREATE TABLE IF NOT EXISTS ffencode_results (
                                        unique_identifier TEXT PRIMARY KEY,
                                        recorded_date TEXT,
                                        file_name TEXT,
                                        file_path TEXT,
                                        config_name TEXT
                                        new_file_size REAL,
                                        new_file_sizeifference REAL, 
                                        old_file_size REAL,
                                        watch_folder TEXT
                                    ); """


    sql_create_configurations_table = """ CREATE TABLE IF NOT EXISTS ffencode_config (
                                        unique_identifier TEXT PRIMARY KEY,
                                        recorded_date TEXT,
                                        file_name TEXT,
                                        file_path TEXT,
                                        config_name TEXT,
                                        ffmpeg_audio_codec TEXT,
                                        ffmpeg_audio_string TEXT,
                                        ffmpeg_container TEXT
                                        ffmpeg_container_extension TEXT,
                                        ffmpeg_container_string TEXT,
                                        ffmpeg_encoding_string TEXT,
                                        ffmpeg_output_file TEXT
                                        ffmpeg_settings TEXT,
                                        ffmpeg_subtitle_format TEXT,
                                        ffmpeg_subtitle_string TEXT,
                                        ffmpeg_video_codec TEXT
                                        ffmpeg_video_string TEXT,
                                        watch_folder TEXT
                                    ); """

    sql_create_source_table = """ CREATE TABLE IF NOT EXISTS ffencode_source (
                                        unique_identifier TEXT PRIMARY KEY,
                                        recorded_date TEXT,
                                        file_name TEXT,
                                        file_path TEXT,
                                        config_name TEXT
                                        original_audio_codec TEXT,
                                        original_container TEXT,
                                        original_subtitle_format TEXT,
                                        original_video_codec TEXT,
                                        watch_folder TEXT
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_projects_table)
        create_table(conn, sql_create_projects_table)  
        create_table(conn, sql_create_projects_table)            
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
























