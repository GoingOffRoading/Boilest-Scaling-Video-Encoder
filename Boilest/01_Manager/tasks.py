from celery import Celery
from datetime import datetime
import json, os, sqlite3, logging
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffmpeg_output_file, ffprober_function, get_active_tasks, get_file_size_bytes
import celeryconfig

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

@app.on_after_configure.connect
# Celery's scheduler.  Kicks off queue_workers_if_queue_empty every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(3600.0, queue_workers_if_queue_empty.s('hit it'))


@app.task(queue='manager')
# Not in use... yet
def purge_queue(queue_name):
    with app.connection() as connection:
        # Create a channel
        channel = connection.channel()
        # Purge the specified queue
        channel.queue_purge(queue=queue_name)
        logging.debug(f"All tasks in the '{queue_name}' queue have been purged.")


@app.task(queue='manager')
# queue_workers_if_queue_empty stops the rest of the workflow from creaing duplicate tasks (because the tasks the rest of the workflow would create would be duplicates of the tasks already in the queue).
def queue_workers_if_queue_empty(arg):
    queue_depth = check_queue('worker') + get_active_tasks('worker') + check_queue('manager') + get_active_tasks('manager')
    logging.debug ('Current Worker queue depth is: ' + str(queue_depth))
    if queue_depth == 0:
        logging.debug ('Starting locate_files')
        locate_files.delay(arg)
    elif queue_depth > 0:
        logging.debug (str(queue_depth) + ' tasks in queue.  No rescan needed at this time.')
    else:
        logging.error ('Something went wrong checking the Worker Queue')

@app.task(queue='manager')
def ffresults(ffresults_input):

    function_start_time = task_start_time('ffresults')

    logging.debug ('Encoding results for: ' + ffresults_input['file'])
    logging.debug ('From: ' + ffresults_input['root']) 

    recorded_date = datetime.now()

    logging.debug ("File encoding recorded: " + str(recorded_date))
    unique_identifier = ffresults_input["file"] + str(recorded_date.microsecond)
    logging.debug ('Primary key saved as: ' + unique_identifier)

    database = r"/Boilest/DB/Boilest.db"
    try:
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute(
            "INSERT INTO ffencode_results"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                unique_identifier,
                recorded_date,
                ffresults_input["file"], 
                ffresults_input["file_path"], 
                ffresults_input["new_file_size"], 
                ffresults_input["new_file_size_difference"], 
                ffresults_input["old_file_size"],
                ffresults_input["ffmpeg_command"],
                ffresults_input["encode_outcome"],
                ffresults_input["original_string"]
            )
        )
        conn.commit()
        
        c.execute("SELECT ROUND(SUM(new_file_size_difference)) FROM ffencode_results")
        result = c.fetchone()[0]
        if result is not None:
            logging.info(f'Total space saved: {result} MB')
        else:
            logging.warning('No records found in ffencode_results table.')
            
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        conn.close()


    logging.info ('The space delta on ' + ffresults_input["file"] + ' was: ' + str(ffresults_input["new_file_size_difference"]) + ' MB')
    task_duration_time('ffresults',function_start_time)


