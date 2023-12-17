docker run --env=Manager=Yes --env=celery_vhost=test  --volume=C:\Users\Chase\media\test_folder:/tv -p 5555:5555 -d worker:latest

docker run --env=celery_vhost=test  --volume=C:\Users\Chase\media\test_folder:/tv  -d worker:latest