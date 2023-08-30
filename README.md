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

Ask me in a few months.

Hypothedically:

* Scans a container volume for media
* Determines actions based on FFProbe outputs (re-encode video, re-encode audio, change subtitle format, change container, etc) against a desired media spec
* Leverages Celery to distrbute FFProbe tasks to worker nodes
* Worker nodes validate their ouputs using libvmaf to quantify the file's accuracy
* Worker replaces the original file with the newely encoded one
* Worker logs job stats (file name, before size, after size, vmaf score)

None of this works today

# What is in this repo today?

Little bits of code that work, and me struggling with the basics to glue it all together