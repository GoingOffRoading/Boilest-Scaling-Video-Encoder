## Manager ToDo List

- [ ] Interactive UI
- [x] Add a status field to the queue DB
- [x] Update flask_post_queue to check for the status flag, instead of checking for datetime columns
- [ ] Maybe add another queue for largest impact.  I.E. Largest file, x264, etc.  Maybe a field like 'encode priorit' or something.  
- [x] Update flast_get_largest_queue to use the same datetime logic as queed/completed for datetime stamp
- [x] Logs were being printed for files being added to queue that were correctly being skipped
- [x] Refactor both pipelines so that /boilemdia/ isn't used in the directory path... I.E. Appear more like the actual URL
- [ ] Develop better SVT-AV1 strings
- [ ] Add SVT-AV1 strings to /Directories in the DB
- [ ] Use these values when encodings
- [ ] Add a skip for HDR content
- [ ] Come up with a strategy for HDR content







libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15


