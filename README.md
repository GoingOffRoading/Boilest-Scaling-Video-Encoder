# Boilest

Boilest is my solution to:

- Having video media in lots of different formats, but wanting to consolidate it into one format
- Having video media consume a lot of disk space, and desiring to compress it
- Wanting to do this work at scale

# Why 'Boilest'?

Because I am terrible at naming things, and it was the first agreeable thing to come out of a random name generator.

# What about Tdarr, Unmanic, or other existing distributed solutions??

[Tdarr](https://home.tdarr.io/) is a great platform, but didn't setup or scale as well as I would have liked.  I also found it dificult to under documented, closed source, had some design oddities, and hid features behind a paywall.

As frenzied as Tdarr fans are on Reddit, I just can't commit/subscribe to a service like that.

[Unmanic](https://github.com/Unmanic/unmanic/tree/master) is magic...  I am a big fan, and Unmanuc is comftorably the inspiration of this project.

I would be using Unmanic today, instead of writing spagetti code, but Josh5 has [hardcoded the platform on an older version of FFmpeg](https://github.com/Unmanic/unmanic/blob/master/docker/Dockerfile#L82), doesn't currently support AV1, [has some complexities to build the container](https://github.com/Unmanic/unmanic/blob/master/docker/README.md) that make it dificult to code my own support, and doesn't seem to be keeping up on the repo or accepting PRs.

# Why not Handbrake?

Handbrake is awesome, but:

- It's not distributed
- It's 'watch folder' functionality doesn't do any file checking, sorting, or filtering to decide if it should actually process a file
- Does not have the functionality for monitoring an existing media collection

# How does Boilest work?

A manager node kicks off a series of tasks:

* Hourly, kick off the workflow
* Continue if the queue is empty
* Scan direcorites for media files
* Probe those media files
* Then work through a progressive workflow of determining which streams, media files, and which codecs in each media file need to be endeded.  If a target media file is already in the desired state, Boilest will not attept to encode it.

The worker(s) pick up the tasks from the manager, and encodes the file (as determined by the manager), then sends some stats back to the manager on success.  

# What is in this repo today?

Little bits of code that work, and me struggling with the basics to glue it all together...  BUT, it all works and is running.

# How to deploy

Can be deployed in Docker or in Kubernetes.  General container and prerequesit information will be belllow. Deployment examples will be in the /Deployment directory.

## Prerequisit 

### RabbitMQ

The backbone of Boilest is a distributed task Python library called [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html). Celery needs a message transport (a place to store the task queue), and we leverage RabbitMQ for that.

RabbitMQ will need to be deployed with it's management plugin.








# Boilest Development Notes





Setting the timezone

Use the TZ identifier here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

ffmpeg -hide_banner -loglevel 16 -stats -r 24 -i newtest.mkv -r 24 -i newtestsrtlaopus.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -


ffmpeg -video_size 3840x2160 -framerate 60 -pixel_format yuv420p10le -i decoded_encoded_h264_55.YUV -video_size 3840x2160 -framerate 60 -pixel_format yuv420p10le -i S01AirAcrobatic_3840x2160_60fps_10bit_420.yuv -lavfi libvmaf="model_path=vmaf_v0.6.1.pkl:log_path=VMAF.txt" -f null -


https://stackoverflow.com/questions/16691161/getting-number-of-messages-in-a-rabbitmq-queue





https://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary


select 
COUNT(DISTINCT unique_identifier) as files_processed, 
sum(new_file_size_difference) as difference,
(SUM(new_file_size_difference)/sum(old_file_size)) as difference2,
sum(new_file_size_difference)/COUNT(DISTINCT unique_identifier) as space_per_file
FROM ffencode_results;



# Q'n A

  * If Celery can use Reddis or RabbitMQ for it's message transport, can Boilest use Reddis?

    Not in Boilest's current state.  Boilest doesn't use any RabbitMQ functionality that Reddis doesn't have an equivilent.  That said, of the to-dos in /Scripts, having message transport flexibility is not a priority at this time.

- Why does Boilest use RabbitMQ over Reddis?

    I happened to have RabbitMQ with the management plugin already installed.