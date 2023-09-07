import json
import os

def ffinder(json_template):
    # Need to change this line to be a variable passed to the function
    # I.E. Invoke the search based on feeding it a JSON
    #f = open(json_template)
    # returns JSON object as
    # a dictionary
    #data = json.load(f)
    #print (data)
    print(json.dumps(json_template, indent=3, sort_keys=True))
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
                ffinder_json = {'file_path':root, 'file_name':file}
                ffinder_json.update(data)      
                print(json.dumps(ffinder_json, indent=3, sort_keys=True))
                yield(ffinder_json)