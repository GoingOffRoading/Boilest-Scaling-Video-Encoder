## Manager ToDo List

- [x] Interactive UI
- [x] Add a status field to the queue DB
- [x] Update flask_post_queue to check for the status flag, instead of checking for datetime columns
- [x] Maybe add another queue for largest impact.  I.E. Largest file, x264, etc.  Maybe a field like 'encode priorit' or something.  
- [x] Update flast_get_largest_queue to use the same datetime logic as queed/completed for datetime stamp
- [x] Logs were being printed for files being added to queue that were correctly being skipped
- [x] Refactor both pipelines so that /boilemdia/ isn't used in the directory path... I.E. Appear more like the actual URL
- [x] Develop better SVT-AV1 strings
- [x] Add SVT-AV1 strings to /Directories in the DB
- [x] Use these values when encodings
- [x] Add a skip for HDR content
- [ ] Later: Come up with a strategy for HDR content
- [x] Add codec types to target in the directories table
- [x] Add a display for currently queued and recently encoded
- [ ] Rewrite repo readme
- [x] Come up with a decision on whether to skip previusly failed files
- [ ] Add logic to the UI for when DB is disabled
- [ ] Add logic for audio
- [ ] Add logic for subtitles
- [ ] Implement some kind of heartbeat for workers.  I.E. Encoded task returns to queue unless worker checks in after X time
- [x] Need to rethink workers.  Like when a task is retrieved, we should log the node.  Then log the state.  So when a worker fails, it might be able to pick up where it left off.
- [x] Make it so that directories are not deleted
- [x] Remember to update Boilest.db after the ffmpeg settings tweaks
- [x] Maybe change directory active boolean to something more intuitive
- [x] Update workers metric to include pulled
- [x] Change encoding time to days.  Or maybe make it dynamic Minutes > Hours > Days










## v3 SVT-AV1 Settings

### Templates

#### Live Action Baseline:

libsvtav1 -crf <CRF> -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### Animated Baseline:

libsvtav1 -crf <CRF> -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

### Directory Settings

#### TV-Live-Action
libsvtav1 -crf 25 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### TV-Animated
libsvtav1 -crf 28 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### TV-Live-Action-Favorites
libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### TV-Animated-Favorites
libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Live-Action
libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Animated
libsvtav1 -crf 23 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Live-Action-Favorites
libsvtav1 -crf 19 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0

#### Movies-Animated-Favorites
libsvtav1 -crf 20 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Anime
libsvtav1 -crf 26 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Anime-Favorites
libsvtav1 -crf 22 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### YouTube
libsvtav1 -crf 25 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=6:qm-max=16:ac-bias=5:tf-strength=1:enable-variance-boost=1:scd=1:filmgrain=0

#### Home-Movies
libsvtav1 -crf 19 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=20:ac-bias=6:tf-strength=2:enable-variance-boost=1:scd=1:filmgrain=0














# v2 SVT-AV1 Settings

### TV_Favorites
libsvtav1 -crf 24 -preset 3 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=6:qm-max=12:filmgrain=0:film-grain-denoise=0

### Movies_Archive
libsvtav1 -crf 30 -preset 5 -g 240 -keyint_min 24 -tile-columns 2 -tile-rows 0 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=8:qm-max=16:filmgrain=0:film-grain-denoise=0

### Movies_Favorites
libsvtav1 -crf 20 -preset 2 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=10:filmgrain=12:film-grain-denoise=1

### Anime_Archive
libsvtav1 -crf 30 -preset 5 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=8:qm-max=15:filmgrain=0:film-grain-denoise=0

### Anime_Favorites
libsvtav1 -crf 22 -preset 3 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=10:filmgrain=0:film-grain-denoise=0

### YouTube_Archive
libsvtav1 -crf 26 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=6:qm-max=12:filmgrain=0:film-grain-denoise=0

### Home_Movies
libsvtav1 -crf 22 -preset 3 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=10:filmgrain=0:film-grain-denoise=0



# Original/v1 SVT-AV1 Settings
## Anime
libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15