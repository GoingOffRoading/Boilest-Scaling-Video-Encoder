import json
import os
import time

def finder(json_file):
    # Need to change this line to be a variable passed to the function
    # I.E. Invoke the search based on feeding it a JSON
    f = open(json_file)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    print (data)

    # Get the folder to scan
    directory = (data['watch_folder'])

    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')

    # traverse whole directory
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4'):
                # append the desired fields to the original json
                finder_data = {'file_path':root, 'file_name':file}
                finder_data.update(data)      
                print(json.dumps(finder_data, indent=3, sort_keys=True))
                yield(finder_data)