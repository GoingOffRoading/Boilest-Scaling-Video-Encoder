from celery import Celery
from datetime import datetime
import sqlite3

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')


@app.task(queue='manager')
def fresults(fencoder_json):
    # Last but not least, record the results of ffencode
    fresults_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fresults for ' + fencoder_json["file_name"] + ' starting at ' + str(fresults_start_time) + '<<<<<<<<<<<<<<<<<<<')
    config_name = fencoder_json["config_name"]
    ffmpeg_encoding_string = fencoder_json["ffmpeg_encoding_string"]
    file_name = fencoder_json["file_name"]
    file_path = fencoder_json["file_path"]
    new_file_size = fencoder_json["new_file_size"]
    new_file_size_difference = fencoder_json["new_file_size_difference"]
    old_file_size = fencoder_json["old_file_size"]
    watch_folder = fencoder_json["watch_folder"]
    fencoder_duration = fencoder_json["fencoder_duration"]
    original_string = fencoder_json["original_string"]
    notes = fencoder_json["notes"]
    override = fencoder_json["override"]
    encode_outcome = fencoder_json["encode_outcome"]

    recorded_date = datetime.now()

    print ("File encoding recorded: " + str(recorded_date))
    unique_identifier = file_name + str(recorded_date.microsecond)
    print ('Primary key saved as: ' + unique_identifier)

    database = r"/Boilest/DB/Boilest.db"
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ffencode_results"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            unique_identifier,
            recorded_date,
            file_name, 
            file_path, 
            config_name,
            new_file_size, 
            new_file_size_difference, 
            old_file_size,
            watch_folder,
            ffmpeg_encoding_string,
            fencoder_duration,
            original_string,
            notes,
            override,
            encode_outcome
        )
    )
    conn.commit()

    c.execute("select round(sum(new_file_size_difference)) from ffencode_results")
    total_space_saved = c.fetchone()
    c.execute("select round(sum(fencoder_duration)) from ffencode_results")
    total_processing_time = c.fetchone()
    conn.close()

    print ('The space delta on ' + file_name + ' was: ' + str(new_file_size_difference) + ' MB and required ' + str(fencoder_duration) + ' minutes of encoding')
    print ('We have saved so far: ' + str(total_space_saved) + ' MB, which required a total processing time of ' + str(total_processing_time) + ' minutes')
      
    fresults_duration = (datetime.now() - fresults_start_time).total_seconds() / 60.0   
    print ('>>>>>>>>>>>>>>>> fencoder ' + fencoder_json["file_name"] + ' complete, executed for ' + str(fresults_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')