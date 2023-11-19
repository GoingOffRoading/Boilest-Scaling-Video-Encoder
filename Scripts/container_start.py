import os, shutil
from task_shared_services import is_directory_empty_recursive, copy_directory_contents

if os.path.isdir('/Boilest/Logs') == False:
    print ('/Boilest/Logs directory does not exist, creating')
    os.mkdir('/Boilest/Logs')
else:
    print ('/Boilest/Logs exists, no action needed')

# Checking for atleast the base configuration

print ('Checking to see if /Boilest/Configurations is empty')
  
# Checking to see if /Boilest/Configurations exists
if os.path.isdir('/Boilest/Configurations') == False:
    print("No Configurations, adding Defualts")
    os.mkdir('/Boilest/Configurations')
else: 
    print("/Configurations exists")

#Check to see if Configurations exist in /Configurations
if is_directory_empty_recursive('/Boilest/Configurations') == False:
    copy_directory_contents('/Scripts/Configurations', 'Boilest/Configurations')

