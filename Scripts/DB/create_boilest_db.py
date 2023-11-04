import os.path, sqlite3

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
        
    except Error as e:
        print(e)

if os.path.exists("/Boilest/DB/Boilest.db"):
    print ('Boilest.db exists')
else:
    print ('Boilest.db does not exist, creating now')
    database = r"/Boilest/DB/Boilest.db"
    
    sql_create_results_table = """ CREATE TABLE IF NOT EXISTS ffencode_results (
                                        unique_identifier TEXT PRIMARY KEY,
                                        recorded_date TEXT,
                                        file_name TEXT,
                                        file_path TEXT,
                                        config_name TEXT,
                                        new_file_size REAL,
                                        new_file_size_difference REAL, 
                                        old_file_size REAL,
                                        watch_folder TEXT,
                                        ffmpeg_encoding_string TEXT,
                                        fencoder_duration REAL,
                                        original_string TEXT,
                                        notes TEXT

                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_results_table)
        conn.close()           
    else:
        print("Error! cannot create the database connection.")

