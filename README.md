# Note

This project is being refactored.  Stay tuned.


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

- Boilest kicks off a job that searches directories for video files
- Boilest then checks each individual video file to see if the various codecs match a spec
- If any of the codecs don't match spec, the file is dispatched for encoding
- Once encoding is complete, the results are stored in a DB

 # What is in this repo today?

A simplified workflow running in Celery

# How to deploy

- Build the container image 
- Deploy the image

See /Deployment for a Kubernetes example using Azure Container Registry

## Prerequisit 

### RabbitMQ

The backbone of Boilest is a distributed task Python library called [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html). Celery needs a message transport (a place to store the task queue), and we leverage RabbitMQ for that.

RabbitMQ will need to be deployed with it's ,management plugin.

# Q&A

  * If Celery can use Reddis or RabbitMQ for it's message transport, can Boilest use Reddis?

    Not in Boilest's current state.  Boilest doesn't use any RabbitMQ functionality that Reddis doesn't have an equivilent.  That said, of the to-dos in /Scripts, having message transport flexibility is not a priority at this time.

- Why does Boilest use RabbitMQ over Reddis?

    I happened to have RabbitMQ with the management plugin already installed.

- What's in /Old?

  A lot of previous itterations/experiments with this project:
  - Different containers for tasks
  - Different queues
  - FFprobe via configuration files
  - Experiments with Flask font end
  - And more
  
  They're worth keeping around for refrences/discussion on [r/learnpython](https://www.reddit.com/r/learnpython/)


# Todo List:

# Todo List

- [x] Setup a set_priority function for ffprobe based on container, file size, and video codec (I.E. the things that have the greatest impact on ROI)
- [x] Setup the function to write the results to the DB
- [x] Replace the prints with logging
- [ ] Made decisions on audio codec
- [ ] Makde decisions on subtitle codec
- [ ] Research ffprobe flags for HDR content
- [x] Figure out how to pass the wath folder forward for the SQL write
- [x] Figure out how to pass the ffmpeg string forward for the SQL write

