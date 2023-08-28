import os

def findmedia(DIRECTORY):
    print('Going to start scanning ' + DIRECTORY)
    # traverse whole directory
    for root, dirs, files in os.walk(DIRECTORY):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4'):
                # print whole path of files
                print(os.path.join(root, file))
