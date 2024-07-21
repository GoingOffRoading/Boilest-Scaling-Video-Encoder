Coming Soon



# Deployment via Docker Desktop and Windows Power Shell

Change directory to /Boilest

    cd Boilest

LS output should look like this

    Directory: C:\Users\YOU\GitHub\Boilest-Scaling-Video-Encoder\Boilest
    Mode                 LastWriteTime         Length Name
    ----                 -------------         ------ ----
    d-----         6/14/2024   3:07 PM                01_Manager
    d-----         7/10/2024   9:30 AM                02_Worker
    d-----         6/14/2024   3:32 PM                Config
    -a----         6/14/2024   3:23 PM             50 readme.md
    PS C:\Users\YOU\GitHub\Boilest-Scaling-Video-Encoder\Boilest>

Build the images (in this example, using Docker Desktop):

    docker build -t manager -f 01_Manager/Dockerfile .
    docker build -t worker -f 02_Worker/Dockerfile .

Run (change the worker volume(s) as needed)

    docker run -p 5000:5000 -p 5555:5555 -d manager:latest
    docker run --volume=C:\Users\YOU\Videos:/tv -d worker:latest