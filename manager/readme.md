## Manager ToDo List

- [x] Interactive UI
- [x] Add a status field to the queue DB
- [x] Update flask_post_queue to check for the status flag, instead of checking for datetime columns
- [ ] Maybe add another queue for largest impact.  I.E. Largest file, x264, etc.  Maybe a field like 'encode priorit' or something.  
- [x] Update flast_get_largest_queue to use the same datetime logic as queed/completed for datetime stamp
- [x] Logs were being printed for files being added to queue that were correctly being skipped
- [x] Refactor both pipelines so that /boilemdia/ isn't used in the directory path... I.E. Appear more like the actual URL
- [x] Develop better SVT-AV1 strings
- [x] Add SVT-AV1 strings to /Directories in the DB
- [x] Use these values when encodings
- [x] Add a skip for HDR content
- [ ] Later: Come up with a strategy for HDR content
- [ ] Before allowing a filebase scan, check if queue is empty
- [x] Add codec types to target in the directories table
- [x] Add a display for currently queued and recently encoded







libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15



### TV_Archive
libsvtav1 -crf 30 -preset 6 -g 240 -keyint_min 24 -tile-columns 2 -tile-rows 0 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=10:qm-max=18:filmgrain=0:film-grain-denoise=0

### TV_Favorites
libsvtav1 -crf 24 -preset 3 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=6:qm-max=12:filmgrain=0:film-grain-denoise=0

### Movies_Archive
libsvtav1 -crf 30 -preset 5 -g 240 -keyint_min 24 -tile-columns 2 -tile-rows 0 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=8:qm-max=16:filmgrain=0:film-grain-denoise=0

### Movies_Favorites
libsvtav1 -crf 20 -preset 2 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=10:filmgrain=12:film-grain-denoise=1

### Anime_Archive
libsvtav1 -crf 30 -preset 6 -g 240 -keyint_min 24 -tile-columns 2 -tile-rows 0 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=12:qm-max=20:filmgrain=0:film-grain-denoise=0

### Anime_Favorites
libsvtav1 -crf 22 -preset 3 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=1:enable-qm=1:qm-min=6:qm-max=10:filmgrain=0:film-grain-denoise=0

### YouTube_Archive
libsvtav1 -crf 26 -preset 4 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=6:qm-max=12:filmgrain=0:film-grain-denoise=0

### Home_Movies
libsvtav1 -crf 22 -preset 3 -g 240 -keyint_min 24 -pix_fmt yuv420p10le -svtav1-params tune=0:enable-qm=1:qm-min=4:qm-max=10:filmgrain=0:film-grain-denoise=0

