
docker build -t worker .

docker run -e Manager=Yes -e celery_vhost=test -e Celery_Log_level=DEBUG --volume=C:\Users\Chase\media\test_folder:/tv -p 5555:5555 -d worker:latest

docker run -e celery_vhost=test  -e Celery_Log_level=DEBUG  --volume=C:\Users\Chase\media\test_folder:/tv  -d worker:latest