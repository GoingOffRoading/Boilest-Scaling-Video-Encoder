# Workflow

This is the Boilest workflow, and work that is currently outstanding 

# To Do List
- [ ] Cron that checks the queue, and injects the find_files task if the queue is empty
- [x] Task that recusively searches directories based on file extensions
- [x] For each file, calls the next step
- [x] Function that calls FFprobe for the file, and determines next step
- [x] Function that calls FFmpeg and processes the file
- [x] Function that moves the encoded file into the source and deletes the soure file
- [x] Function that checks the files size of the new and old file
- [x] Configuration based
- [ ] Logging
- [ ] Writing results of the ffencode step to SQLite
- [x] Starts workflow based on a JSON configuration
- [ ] Rewrite the FFProbe section to handle when a media file doesn't have a video, audio, or subtitle stream
- [ ] Expirement with AV1 film grain: https://www.google.com/search?q=av1+film+grain+synthesis+anime
- [ ] Expirement with subtitle settings
- [ ] Experiement with audio codec settings
- [ ] Django project
- [ ] UI Design
- [ ] UI