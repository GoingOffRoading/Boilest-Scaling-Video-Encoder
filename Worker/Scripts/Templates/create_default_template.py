import os, shutil

path = "/Boilest/Configurations"
# Getting the list of directories 
dir = os.listdir(path) 
  
# Checking if the list is empty or not 
if len(dir) == 0: 
    print("No COnfigurations, adding Defualt")
    shutil.copyfile('/Scripts/Templates/AV1_CRF20Preset4.json', '/Boilest/Configurations/AV1_CRF20Preset4.json') 
else: 
    print("Configurations detected, no action to take") 

