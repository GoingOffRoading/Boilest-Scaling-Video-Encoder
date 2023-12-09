import os, shutil

if os.path.isdir('/Boilest/Logs') == False:
    print ('/Boilest/Logs directory does not exist, creating')
    os.mkdir('/Boilest/Logs')
else:
    print ('/Boilest/Logs exists, no action needed')

# Checking for atleast the base configuration

print ('Checking to see if /Boilest/Configurations is empty')

def check_and_copy_directory(source_dir, destination_dir):
    # Check if the destination directory exists
    if not os.path.exists(destination_dir):
        print(f"Destination directory does not exist. Creating {destination_dir}.")
        os.makedirs(destination_dir)

    # Check if the destination directory is empty
    if not os.listdir(destination_dir):
        print("Destination directory is empty. Copying files and directories.")
        copy_files_and_directories(source_dir, destination_dir)
    else:
        print("Destination directory is not empty. Skipping copy.")

def copy_files_and_directories(source_dir, destination_dir):
    for item in os.listdir(source_dir):
        source_item = os.path.join(source_dir, item)
        destination_item = os.path.join(destination_dir, item)

        if os.path.isdir(source_item):
            # Recursively copy directories
            shutil.copytree(source_item, destination_item)
        else:
            # Copy files
            shutil.copy2(source_item, destination_item)


source_directory = "/Scripts/DB"
destination_directory = "/Boilest/DB"

check_and_copy_directory(source_directory, destination_directory)


