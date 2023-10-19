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

* A script scans a container volume for media.  Each file discovered is individually sent to an FFprobe function to determine if the file should be reencoded.
* An FFProbe function scans each discovered piece of media and determines actions based on FFProbe outputs (re-encode video, re-encode audio, change subtitle format, change container, etc).  The decision is made against a configuration.  Any files determined to require encoding are sent to the next step.
* Media files passed  from the FFprobe step are encoded using FFmpeg.  Once the file is done encoding, it is compared to the original.  If the comparison passes, the original file is replaced, and file stats are sent to the next step.
* All encoded file states from the FFmpeg step are recorded in a SQL database.

This works end to end.  I'm on the fence about having the scan kick off at launch...  TBD...  The end goal is to have a configuration UI, but I am a little ways away from that step.

# What is in this repo today?

Little bits of code that work, and me struggling with the basics to glue it all together

# How to deploy

https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes/



## RabbitMQ

* Go into the Admin pannel, and create a vhost 'celery'
* Then go into user pannel, and create a user 'celery', with password 'celery', access to the 'celery' vhost, and admin


# Boilest Development Notes





Setting the timezone

Use the TZ identifier here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

ffmpeg -hide_banner -loglevel 16 -stats -r 24 -i newtest.mkv -r 24 -i newtestsrtlaopus.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -


ffmpeg -video_size 3840x2160 -framerate 60 -pixel_format yuv420p10le -i decoded_encoded_h264_55.YUV -video_size 3840x2160 -framerate 60 -pixel_format yuv420p10le -i S01AirAcrobatic_3840x2160_60fps_10bit_420.yuv -lavfi libvmaf="model_path=vmaf_v0.6.1.pkl:log_path=VMAF.txt" -f null -


https://stackoverflow.com/questions/16691161/getting-number-of-messages-in-a-rabbitmq-queue





https://stackoverflow.com/questions/5844672/delete-an-element-from-a-dictionary