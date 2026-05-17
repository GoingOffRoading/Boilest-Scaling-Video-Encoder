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

[Tdarr](https://home.tdarr.io/) is a great platform, but didn't setup or scale as well as I would have liked.  I also found it to be under documented, closed source, had some design oddities, and hid features behind a paywall.

As frenzied as Tdarr fans are on Reddit, I just can't commit/subscribe to a service like that.

[Unmanic](https://github.com/Unmanic/unmanic/tree/master) is magic...  I am a big fan, and Unmanic is comfortably the inspiration of this project.

I would be using Unmanic today, instead of writing spaghetti code, but Josh5 had previously [hardcoded the platform to a version of FFmpeg](https://github.com/Unmanic/unmanic/blob/master/docker/Dockerfile#L82) that didn't support AV1 (SVT-AV1), [and has some complexities to build the container](https://github.com/Unmanic/unmanic/blob/master/docker/README.md) that make it difficult to code my own support.  I have not check on the progress of Unmanic to see if this was updated.  

---
# Why not Handbrake?

Handbrake is awesome, but:

- It's not distributed/doesn't scale past the node with the GUI open
- It's 'watch folder' functionality doesn't do any file checking, sorting, or filtering to decide if it should actually process a file
- Does not have the functionality for monitoring an existing media collection

---
# How does Boilest work?

Boilest is a two step pipeline:

## Manager

- Search pre-configured directories for video media files
- Probe the files for the details of their video, audio, subtitle, attachment streams
- Determine if any of the streams do not meet the pre-configured requirements
- Set a queue of tasks to encoded those files to meet those configured requirements 

## Worker 

- Get the task from the Manager
- Go through a series of pre-flight checks:
    - Validate that the video file still exists
    - Validate that it's the same video file that was previously scanned
- Assuming pre-flight checks pass
    - Encode the video (this does not affect the source file yet)
- Assuming encoding the video is sucsesful, go through a series of post-flight checks:
    - Validate that the encoded file in the temp directory exists
    - Validate the integrity of the video (no sense in replacing source if the encoded video file is broken)
- Assuming post-vlight checks pass:
    - Delete the source video file
    - Move the encoded video file from the temp directory to the source one
    - Report the outcome back to the Manager

---
 # What will Boilest change?

 In any given media file:

 | Area | Target Change |
 |------|---------------|
 | Container | Media containers that are not MKR (like MP4) are changed to MKV
 | Video | Video streams that are not AV1 are encoded to AV1
 | Audio | Re-encoing audio streams will come in V3. Audio streams in V2 are copied unless they are OPUS.  OPUS has oddities that can break video streams, and are hard-coded to re-encode to AAC Stereo.
 | Subtitles | Re-encoing subtitle streams will come in V3. Subtitle streams in V2 are copied.
 | Attachments | No changes to Attachments at this time.  Attachments are copied.

# What if there is a problem with the file?

Like a bad audio stream, incomplete video streams, etc

- These files will fail their pre-flight checks 
- Boilest will not encode a broken source file, nor will it replace a source file if the encoded one is broken in any way
- Failures are captured in the 'Recently Failed' tab

---
# How to deploy

- Create your deployment (Docker/Kubernetes/etc) with the ghcr.io/goingoffroading/boilest:latest container image.
- Change the container variables to reflect your environment:

| Container | ENV                | Default Value                                                | Notes |
|-----------|--------------------|------------------------------------------------------------- |-------|
| Both      | Role          | Worker                                               | Set the manager containeanagerr as 'Manager' Required if      |
| Manager   | FLASK_APP          | Flask.py                                                     |       |
| Manager   | FLASK_ENV          | development                                                  |       |
| Manager   | FLASK_RUN_HOST     | 0.0.0.0                                                      |       |
| Manager   | FLASK_RUN_PORT     | 5000                                                         |       |
| Manager   | TZ                 | US/Pacific                                                   |       |
| Both      | LOG_LEVEL          | INFO                                                         | What level of logs to dump into the terminal.  Debug will show every step + debug messages.      |
| Worker    | FFMPEG_SETTINGS    | ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i | Useful if you want specific messages dumped by ffmpeg in debug      |  
| Worker    | MANAGER_BASE_URL   | http://localhost:5000                                        |  The IP + Port of the Manager     |
| Worker    | NODE_NAME          | Hostname                                                     |  Aliasing the worker   |

Note: The pipeline requires one Manager container.

- Configured your volumes as needed:

| Contaienr | Directory | Notes |
|-----------|-----------|-------|
| Manager | /boil/app | Required if Persisted application data root |
| Both | /tv-live-action | Live-action TV profile directory |
| Both | /tv-live-action-favorites | Higher-quality live-action TV profile |
| Both | /tv-animated | Animated TV profile directory |
| Both | /tv-animated-favorites | Higher-quality animated TV profile |
| Both | /movies-live-action | Live-action movie profile directory |
| Both | /movies-live-action-favorites | Higher-quality live-action movie profile |
| Both | /movies-animated | Animated movie profile directory |
| Both | /movies-animated-favorites | Higher-quality animated movie profile |
| Both | /anime | Anime profile directory |
| Both | /anime-favorites | Higher-quality anime profile |
| Both | /youtube | YouTube media profile directory |
| Both | /home-movies | Home videos profile directory |

- Deploy 

# What media directories come pre-loaded?

Boilest is bootstrapped with directories that are turnkey with:

- Directory in the container exists
- Each directory is themed with common use-cases
- Boilest comes pre-loaded with an FFMpeg/SVT-AV1 string for that use-case.  

## Bootrapped directories

### TV-Live-Action
- /tv-live-action
- For live-action TV shows
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 25 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### TV-Animated
- /tv-animated
- For animated TV shows
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 28 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### TV-Live-Action-Favorites
- /tv-live-action-favorites
- For live-action TV favorites where picture quality might be a little more important than file size savings or encode time.
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### TV-Animated-Favorites
- /tv-animated-favorites
- For animated TV favorites where picture quality might be a little more important than file size savings or encode time.
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Live-Action
- /movies-live-action
- For live-action movies
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Animated
- /movies-animated
- For animated movies
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 23 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Live-Action-Favorites
- /movies-live-action-favorites
- For live-action movie favorites where picture quality might be a little more important than file size savings or encode time.
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 19 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Animated-Favorites
- /movies-animated-favorites
- For animated movie favorites where picture quality might be a little more important than file size savings or encode time.
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 20 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Anime
- /anime
- For anime series and films
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 26 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Anime-Favorites
- /anime-favorites
- For anime favorites where picture quality might be a little more important than file size savings or encode time.
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### YouTube
- /youtube
- For YouTube videos
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 25 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Home-Movies
- /home-movies
- For home videos and personal recordings
- Preloaded tuned SVT-AV1 String: libsvtav1 -crf 19 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

---
# Can I change the bootstrapped directories, their settings, or setup new ones?

- Yes.  Go to the settings tab in the UI, and all of the options to Add/Remove/Modify are there.

---
# How to start the Boilest/video encoding workflow
Jump into the UI, click the 'Scan for Files' button in the Queued Files


---
# How much of this is GenAI?
- UI: Everything in the UI is GitHub CoPilot.  I am bad at CSS and JavaScript is giberish.  
- Backend is largest hand written.  CoPilot was used to create templates or bootstrap a file, but I found that regardless of model, CoPilot halucinated too much to use to create the full pipelines.  I plan to refactor the endpoints and etc in V3.  

---
# TOS
- Yes!  This is a hobby project of mine and not a fully supported enterprise piece of software.  V2 is being released wth >10,000 files encoded, so my confidence is high that there are no breaking bugs, but you are to use this at your own risk.  I recommend doing a few test batches before encoding anything so that you are comfortable with the UI, directories, FFMpeg/SVT-AV1 settings, and have had an opportunity to make adjustments as you see fit.  I am not responsible for your use or mis-use of ffmpeg.  