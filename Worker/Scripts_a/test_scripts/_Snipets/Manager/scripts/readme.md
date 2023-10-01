# Workflow

This is the Boilest workflow, and work that is currently outstanding 

# Phase One - Basics
Phase one is a basic working pipeline

## Start UI

- [ ] Start Flower

## Start workflow 

- [ ] Cron that checks the queue, and injects the find_files task if the queue is empty

## Find Media Files

- [x] Task that recusively searches directories based on file extensions
- [x] For each file, calls the next step

## Determine if the Media File needs to be prpocessed

- [x] Function that calls FFprobe for the file, and determines next step
- [ ] For each file, calls the next step

## Process the file

- [ ] Function that calls FFmpeg and processes the file

# Phase Two - Configuration & Logging
Phase two will bring three major pieces to the workflow:

- Configuration based
- Logging to container
- Writing results to SQL
- Container startup starts jobs based on container config

## Start UI

## Start workflow 

- [ ] Starts workflow based on a JSON configuration
- [ ] Posts events to teh container

## Find Media Files

- [ ] Appends found file to the JSON configuration
- [ ] Posts events to teh container

## Determine if the Media File needs to be prpocessed

- [ ] Appends found file to the JSON configuration
- [ ] Posts events to teh container

## Process the file

- [ ] Posts events to teh container
- [ ] Pass JSON to the write SQL step

## Write to the SQL

- [ ] Posts events to teh container
- [ ] Write the JSON to SQlite 

# Phase Three - GUI and Function Optimization

- Add a GUI via Django
- Create the plugin templte in Github
- Optimize the functions

## Start UI

- [ ] Add Django to the repo
- [ ] Add a UI element to determine how many jobs are in the queue
- [ ] Add a UI element to query how much data has been saved

## Start workflow 

- [ ] Optimize the function

## Find Media Files

- [ ] Optimize the function

## Determine if the Media File needs to be prpocessed

- [ ] Optimize the function

## Process the file

- [ ] Optimize the function

## Write to the SQL

- [ ] Optimize the function
