import os, shutil

path = "/Boilest/Configurations"
# Getting the list of directories 
dir = os.listdir(path) 
  
# Checking if the list is empty or not 
if len(dir) == 0: 
    print("No Configurations, adding Defualts")
    shutil.copytree('/Scripts/Templates', '/Boilest/Configurations') 
else: 
    print("Configurations detected, no action to take") 

