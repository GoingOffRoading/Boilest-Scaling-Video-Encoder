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