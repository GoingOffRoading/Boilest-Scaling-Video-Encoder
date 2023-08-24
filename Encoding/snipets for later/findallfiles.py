import os
# traverse whole directory
for root, dirs, files in os.walk(r'\\192.168.1.200\Hephaestus\Media'):
    # select file name
    for file in files:
        # check the extension of files
        if file.endswith('.mp4'):
            # print whole path of files
            print(os.path.join(root, file))