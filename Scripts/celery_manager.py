from celery import Celery
from datetime import datetime
import json, os, sqlite3, requests
from celery_worker import fencoderworker

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')


@app.on_after_configure.connect
# Celery's scheduler.  Kicks off ffconfigs every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
def setup_periodic_tasks(sender, **kwargs):
    # Calls ffconfigs('hello') every 10 seconds.
    sender.add_periodic_task(3600.0, ffconfigs.s('hit it'))


@app.task(queue='manager')
# Scan for condigurations, and post the to the next step
# Kicked off by the scheduler above, but started manually with start.py in /scripts
def ffconfigs(arg):
    ffconfig_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffconfigs with the arg: ' + arg + ' starting at ' + str(ffconfig_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # First, we need to check the queue depth.  We don't want to add to queue, or add duplicate tasks, if there are already tasks in the queue 
    worker_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/worker', auth=('celery', 'celery'))).text)
    worker_queue_messages_unacknowledged = (worker_queue["messages_unacknowledged"])
    manager_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/manager', auth=('celery', 'celery'))).text)
    manager_queue_messages_unacknowledged = (manager_queue["messages_unacknowledged"])     
    tasks = worker_queue_messages_unacknowledged + manager_queue_messages_unacknowledged
    
    directory = '/Boilest/Configurations'
    # Searching for configurations
    if tasks == 0:
        print ('No tasks in queue, starting search for configs')
        for root, dirs, files in os.walk(directory):
            # select file name
            for file in files:
                # check the extension of files
                if file.endswith('.json'):
                    # append the desired fields to the original json
                    json_file = os.path.join(root,file)
                    print (json_file)
                    f = open(json_file)
                    json_template = json.load(f)
                    print (json.dumps(json_template, indent=3, sort_keys=True))
                    print ('sending ' + json_template["config_name"] + ' to ffinder')
                    ffinder.delay(json_template)
                else:
                    print('Did not find Configurations')
    elif tasks != 0:
        print ('Tasks in queue: ' + str(tasks) + ', not starting config scan')
    else:
        print ('Tasks in queue returned with an error')
    ffconfig_duration = (datetime.now() - ffconfig_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffconfigs ' + arg + ' complete, executed for ' + str(ffconfig_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')


@app.task(queue='manager')
def ffinder(json_template):
    # The purpose of this function of to search a directory for files, filter for specific formats, and send those filtered results to the next function
    ffinder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffinder executing with config: ' + json_template["config_name"] + ' starting at ' + str(ffinder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # For fun/diagnostics
    print (json.dumps(json_template, indent=3, sort_keys=True))

    # Get the folder to scan
    directory = (json_template['watch_folder'])
    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')

    # traverse whole directory
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
                # append the desired fields to the original json
                ffinder_json = {'file_path':root, 'file_name':file}
                ffinder_json.update(json_template)      
                print(json.dumps(ffinder_json, indent=3, sort_keys=True))
                fencoder.delay(ffinder_json)
                if (json_template["task"]) == 'encode':
                    print ('send task to encode thing this is a placeholder')
                else:
                    print ('placeholder')
    ffinder_duration = (datetime.now() - ffinder_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffinder config: ' + json_template["config_name"] + ' complete, executed for ' + str(ffinder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

@app.task(queue='manager')
def fencoder(ffinder_json):
    fencoder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fencoder executing with config: ' + ffinder_json["config_name"] + ' starting at ' + str(fencoder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    fencoder_json = fencoderworker.delay(ffinder_json)
 
    if fencoder_json["encoded"] == 'no':
        print (fencoder_json["file_name"] + ' was not encoded ')
    elif fencoder_json["encoded"] == 'yes':
        print('Sending task to be recordered in fresults')
        fresults.delay(fencoder_json)
    else:
        print('fencoder failed')
    fencoder_duration = (datetime.now() - fencoder_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> fencoder config: ' + ffinder_json["config_name"] + ' complete, executed for ' + str(fencoder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')



@app.task(queue='manager')
def fresults(fencoder_json):
    # Last but not least, record the results of ffencode
    fresults_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fresults for ' + fencoder_json["file_name"] + ' starting at ' + str(fresults_start_time) + '<<<<<<<<<<<<<<<<<<<')
    config_name = (fencoder_json["config_name"])
    ffmpeg_encoding_string = (fencoder_json["ffmpeg_encoding_string"])
    file_name = (fencoder_json["file_name"])
    file_path = (fencoder_json["file_path"])
    new_file_size = (fencoder_json["new_file_size"])
    new_file_size_difference = (fencoder_json["new_file_size_difference"])
    old_file_size = (fencoder_json["old_file_size"])
    watch_folder = (fencoder_json["watch_folder"])
    fencoder_duration = ((fencoder_json["fencoder_duration"]))

    recorded_date = datetime.now()
    print ("File encoding recorded: " + str(recorded_date))
    unique_identifier = file_name + str(recorded_date.microsecond)
    print ('Primary key saved as: ' + unique_identifier)

    database = r"/Boilest/DB/Boilest.db"
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ffencode_results"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
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
            fencoder_duration
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