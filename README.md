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
- Boilest then checks each individual video file to see if the various codecs match a spec.  In this step, Boilest will also prioritize files that have the highest ROI for encoding first as to not waste time with diminishing returns up front. If any of the codecs don't match spec, the file is dispatched for encoding.
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

| Container | ENV                | Default Value                                                | Notes |
|-----------|--------------------|------------------------------------------------------------- |-------|
| Manager   | FLASK_APP          | Flask.py                                                     |       |
| Manager   | FLASK_ENV          | development                                                  |       |
| Manager   | FLASK_RUN_HOST     | 0.0.0.0                                                      |       |
| Manager   | FLASK_RUN_PORT     | 5000                                                         |       |
| Manager   | TZ                 | US/Pacific                                                   |       |
| Both      | Role               | Worker                                                       |       |
| Both      | LOG_LEVEL          | INFO                                                         | What level of logs to dump into the terminal.  Debug will show every step + debug messages.      |
| Worker    | FFMPEG_SETTINGS    | ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i | Useful if you want specific messages dumped by ffmpeg in debug      |  
| Worker    | POLL_INTERVAL      | 60                                                           |  Measured in seconds.  This is how long the Workers will wait before pinging the Manager for additional tasks.     |
| Worker    | MANAGER_BASE_URL   | http://localhost:5000                                        |  The IP + Port of the Manager     |

- Deploy the container.
- SSH into any one of the containers and run 'python start.sh'.  This will kick off all of the workflows.

Done.

- See 'boilest_kubernetes.yml' for an example of a Kubernetes deployment

---
# How to start the Boilest/video encoding workflow
Jump into the UI, click the start queue button


---
# How much of this is GenAI?
- Everything but the UI: This was largely a refactoring of my existing code.  So GitHub copilot was used to setup some patterns, and the rest was done by hand.  Sans post_completed_encode.py.  I should have seperated this API into multiple (sucess, failure, delete, etc) but got lazy.
-UI: Everything is GitHub CoPilot.  I am bad at CSS and JavaScript is giberish.  