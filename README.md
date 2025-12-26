# EDIT

Hey fun people.  I ran this pipeline for close to two years, and it shaved nearly 10Tb out of my NAS.  Awesome!  But there is clearly room for improvement so a V2 is on the way:

- Moving from an external MySql database to an internal SQLite database
- Startup scripts to check for RabbitMQ setup, DB setup, etc
- Propper HDR support in V2.1
- Audio optimization
- Status US

This is a work in progress in the dev branch.


# Abstraction

Boilest is my solution to:

- Having video media in lots of different formats, but wanting to consolidate it into one format
- Wanting my video content to consume less space in my NAS
- Wanting to do this work at scale

---
# Why 'Boilest'?

Because I am terrible at naming things, and it was the first agreeable thing to come out of a random name generator.

---
# What about Tdarr, Unmanic, or other existing distributed solutions??

[Tdarr](https://home.tdarr.io/) is a great platform, but didn't setup or scale as well as I would have liked.  I also found it comfortably to under documented, closed source, had some design oddities, and hid features behind a paywall.

As frenzied as Tdarr fans are on Reddit, I just can't commit/subscribe to a service like that.

[Unmanic](https://github.com/Unmanic/unmanic/tree/master) is magic...  I am a big fan, and Unmanic is comfortably the inspiration of this project.

I would be using Unmanic today, instead of writing spaghetti code, but Josh5 had previously [hardcoded the platform on an older version of FFmpeg](https://github.com/Unmanic/unmanic/blob/master/docker/Dockerfile#L82), doesn't currently support AV1, [has some complexities to build the container](https://github.com/Unmanic/unmanic/blob/master/docker/README.md) that make it difficult to code my own support, and doesn't seem to be keeping up on the repo or accepting PRs.

---
# Why not Handbrake?

Handbrake is awesome, but:

- It's not distributed/doesn't scale past the node with the GUI open
- It's 'watch folder' functionality doesn't do any file checking, sorting, or filtering to decide if it should actually process a file
- Does not have the functionality for monitoring an existing media collection

---
# How does Boilest work?

- Boilest kicks off a job that searches directories for video files
- Boilest then checks each individual video file to see if the various codecs match a spec.  In this step, Boilest will also prioritize files that have the highest ROI for encoding (large media, x264, mp4, etc) first as to not waste time with diminishing returns (changing small, x265, mkv files) up front. If any of the codecs don't match spec, the file is dispatched for encoding.
- If it is determined from the above step that encoding is required, the file undergoes a series of validations.  Assuming the file passes those validations, the file is encoded.  The output encoded file is then also validated.  If the output encoded file passes validations, it replaces the original file.
- Once encoding is complete, the results are stored in a DB for stats.

---
 # What will Boilest change?

 In any given media file:

 | Area | Target Change |
 |------|---------------|
 | Container | Media containers that are not MKR (like MP4) are changed to MKV
 | Video | Video streams that are not AV1 are encoded to AV1
 | Audio | No changes to audio streams at this time.  Audio streams are copied.
 | Subtitles | No changes to subtitle streams at this time.  subtitle streams are copied.
 | Attachments | No changes to Attachments at this time.  Attachments are copied.

 Once I make some final decisions around what is optimal for TV/device streaming, there will become targets to audio, subtitles, and attachments.

---
# Prerequisites  

---
## RabbitMQ

The backbone of Boilest is a distributed task Python library called [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html). Celery needs a message transport (a place to store the task queue), and we leverage RabbitMQ for that.

RabbitMQ will need to be deployed with it's management plugin.

From the management plugin:

- Create a 'celery' vhost
- Create a user with the user/pwd of celery/celery
- Give the celery .* configure, write, read permissions in the celery vhost

---
## MariaDB

Technically, the workflow works fine (at this time) without access to MariaDB (mysql).  MariaDB is where the results of the encoding are tracked.  If Maria is not deployed, the final task will fail, and this will only be noticeable in the logs.

In Maria, create a database called 'boilest'.

In the 'boilest' database, create a table called 'ffmpeghistory' with the following columns:

| Column Name              | Type                            |
|--------------------------|---------------------------------|
| unique_identifier        | varchar(100)                    |
| recorded_date            | datetime                        |
| file_name                | varchar(100)                    |
| file_path                | varchar(100)                    |
| config_name              | varchar(100)                    |
| new_file_size            | int(11)                         |
| new_file_size_difference | int(11)                         |
| old_file_size            | int(11)                         |
| watch_folder             | varchar(100)                    |
| ffmpeg_encoding_string   | varchar(1000)                   |

In a future iteration, I'll include a python script that populates database and table into Maria automatically.

---
# How to deploy

- Create your deployment (Docker/Kubernetes/etc) with the ghcr.io/goingoffroading/boilest-worker:latest container image.
- Change the container variables to reflect your environment:

| ENV                             | Default Value           | Notes                                               |
|---------------------------------|-------------------------|-----------------------------------------------------|
| celery_user                     | celery                  | The user setup for Celery in your RabbitMQ          |
| celery_password                 | celery                  | The password setup for Celery in your RabbitMQ      |
| celery_host                     | 192.168.1.110           | The IP address of RabbitMQ                          |
| celery_port                     | 31672                   | The port RabbitMQ's port 5672 or 5673 are mapped to |
| celery_vhost                    | celery                  | The RabbitMQ vhost setup for Boilest                |
| rabbitmq_host                   | 192.168.1.110           | The IP address of RabbitMQ management UI            |
| rabbitmq_port                   | 32311                   | The port of RabbitMQ management UI                  |
| sql_host                        | 192.168.1.110           | The IP address of MariaDB                           |
| sql_port                        | 32053                   | The port mapped to MariaDB's port 3306              |
| sql_database                    | boilest                 | The database name setup for Boilest                 |
| sql_user                        | boilest                 | The username setup for Boilest                      |
| sql_pswd                        | boilest                 | The password setup for Boilest                      |

- Deploy the container.
- SSH into any one of the containers and run 'python start.sh'.  This will kick off all of the workflows.

Done.

- See 'boilest_kubernetes.yml' for an example of a Kubernetes deployment

---
# How to start the Boilest/video encoding workflow
Either:
- Deploy the [Boilest Management GUI](https://github.com/GoingOffRoading/Boilest_Manager_GUI) container and either wait for the cron, or SSH into the container and start start.py
- SSH into one of the Boilest-Worker containers and run start.py:

In both SSH cases, literally run
```
python start.py  
```
SSH in Kuberentes is:

```
kubectl exec -it (your pod name) -- /bin/sh
```

SSH in Docker is:

```
docker exec -it (container ID) /bin/sh
```
Starting the workflow only needs to be done once from any one of the relevant containers.  That start will trickle into the other containers via the RabbitMQ broker.

---
# Q&A

  * If Celery can use Redis or RabbitMQ for it's message transport, can Boilest use Redis?

    Not in Boilest's current state, and probably never.  Redis doesn't 'support' prioritization of messages technically at all or as well as rabbit does.  Boilest currently uses RabbitMQ's prioritization of messages to encode the video files with the highest ROI for encoding time.


---
# Todo List

- [x] Setup a set_priority function for ffprobe based on container, file size, and video codec (I.E. the things that have the greatest impact on ROI)
- [x] Setup the function to write the results to the DB
- [x] Replace the prints with logging
- [ ] Made decisions on audio codec
- [ ] Make decisions on subtitle codec
- [ ] Research ffprobe flags for HDR content
- [x] Figure out how to pass the watch folder forward for the SQL write
- [x] Figure out how to pass the ffmpeg string forward for the SQL write
- [x] Stand up repo for management UI
- [ ] Make tweaks to the prioritization scoring
- [ ] Create a 'create database, table' script
- [ ] Having write_results be it's own task is stupid.  Incorporate it into process_ffmpeg.
- [ ] Tasks.py is stupidly big.  Break it up into different files for readability/management.
- [ ] Revisit string formatting i.e. f"Name: {name}, Age: {age}" instead of  name + ", Age:" + str(age)
- [ ] Explore using the Pydantic Model 
- [ ] Remove hard-coding related 
- [ ] Move UniqueID in the SQL to a GUID
- [ ] Explore using pathlib instead of OS
- [x] Remove the archive
- [ ] Some day...  Remove the celery task function for write_results
- [x] Consider moving queue_workers_if_queue_empty to the manager container