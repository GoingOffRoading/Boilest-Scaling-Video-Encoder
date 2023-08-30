# Workflow

This is the Boilest workflow, and work that is currently outstanding 

# Phase One - Basics
Phase one is a basic working pipeline

## Start workflow 

- [ ] Cron that checks the queue, and injects the find_files task if the queue is empty
- [ ] Starts workflow based on a JSON configuration

## Find Media Files

- [x] Task that recusively searches directories based on file extensions
- [x] For each file, calls the next step
- [ ] Optimize the function 
- [ ] Appends found file to the JSON configuration

## Determine if the Media File needs to be prpocessed

- [x] Function that calls FFprobe for the file, and determines next step
- [ ] For each file, calls the next step
- [ ] Optimize the function 
- [ ] Appends found file to the JSON configuration

## Process the file

- [ ] Function that calls FFmpeg and processes the file

# Phase Two - Configuration & Logging
Phase two will bring three major pieces to the workflow:

- Configuration based
- 