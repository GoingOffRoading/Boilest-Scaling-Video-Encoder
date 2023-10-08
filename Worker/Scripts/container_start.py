import os

if os.path.isdir('/Boilest/DB') == False:
    print ('/Boilest/DB directory does not exist, creating')
    os.mkdir('/Boilest/DB')
else:
    print ('/Boilest/DB exists, no action needed')

if os.path.isdir('/Boilest/Configurations') == False:
    print ('/Boilest/Configurations directory does not exist, creating')
    os.mkdir('/Boilest/Configurations')
else:
    print ('/Boilest/Configurations exists, no action needed')