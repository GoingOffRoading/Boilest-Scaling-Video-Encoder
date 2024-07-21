# Boilest

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

[Unmanic](https://github.com/Unmanic/unmanic/tree/master) is magic...  I am a big fan, and Unmanuc is comftorably the inspiration of this project.

I would be using Unmanic today, instead of writing spagetti code, but Josh5 had previously [hardcoded the platform on an older version of FFmpeg](https://github.com/Unmanic/unmanic/blob/master/docker/Dockerfile#L82), doesn't currently support AV1, [has some complexities to build the container](https://github.com/Unmanic/unmanic/blob/master/docker/README.md) that make it difficult to code my own support, and doesn't seem to be keeping up on the repo or accepting PRs.

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
# How to deploy

- Create your deployment (Docker/Kubernetes/etc) with the ghcr.io/goingoffroading/boilest-worker:latest container image.
- Change the container variables to reflect your environment:

| ENV                 | Defaul Value  |
|---------------------|---------------|
| user                | celery        |
| password            | celery        |
| celery_host         | 192.168.1.110 |
| celery_port         | 31672         |
| celery_vhost        | celery        |
| rabbitmq_host       | 192.168.1.110 |
| rabbitmq_port       | 32311         |
| sql_host            | 192.168.1.110 |
| sql_port            | 32053         |
| sql_database        | boilest       |
| sql_user            | boilest       |
| sql_pswd            | boilest       |

- Deploy the container.
- SSH into any one of the containers and run 'python start.sh'.  This will kick off all of the workflows.

Done.

- See 'boilest_kubernetes.yml' for an example of a Kubernetes deployment

---
# Prerequisit 

---
## RabbitMQ

The backbone of Boilest is a distributed task Python library called [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html). Celery needs a message transport (a place to store the task queue), and we leverage RabbitMQ for that.

RabbitMQ will need to be deployed with it's management plugin.

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

In a huture itteration, I'll include a python script that populates database and table into Maria automatically.

---
# Q&A

  * If Celery can use Redis or RabbitMQ for it's message transport, can Boilest use Redis?

    Not in Boilest's current state, and probably never.  Redis doesn't 'support' prioritization of messages technically at all or as well as rabbit does.  Boilest currently uses RabbitMQ's prioritization of messages to encode the video files with the highest ROI for encoding time.

- What's in /Old?

  A lot of previous iterations/experiments with this project:
  - Different containers for tasks
  - Different queues
  - FFprobe via configuration files
  - Experiments with Flask font end
  - And more
  
  They're worth keeping around for references/discussion on [r/learnpython](https://www.reddit.com/r/learnpython/)

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
- [ ] Stand up repo for management UI
- [ ] Make tweaks to the priotiziation scoring
- [ ] Create a 'create database, table' script
- [ ] Having write_results be it's own task is stupid.  Incorporate it into process_ffmpeg.
- [ ] Tasks.py is stupidly big.  Break it up into different files for readability/management.
- [ ] Revisit string formatting i.e. f"Name: {name}, Age: {age}" instead of  name + ", Age:" + str(age)
- [ ] Explore using the Pydantic Model 
- [ ] Remove hard-coding related 
- [ ] Move UniqueID in the SQL to a GUID
- [ ] Explore using pathlib instead of OS
- [x] Remove the archive
