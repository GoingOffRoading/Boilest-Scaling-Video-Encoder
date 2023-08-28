import os


print('Goingto start scanning ' + os.environ['DIRECTORY'])
# traverse whole directory
for root, dirs, files in os.walk(r'\boil_watch'):
    # select file name
    for file in files:
        # check the extension of files
        if file.endswith('.mkv'):
            # print whole path of files
            print(os.path.join(root, file))
