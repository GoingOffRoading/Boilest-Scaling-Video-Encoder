#!/bin/sh

# Run manager container

docker run --env=Role=Manager --volume=C:\Users\cwest\btest:/boil/app --volume=C:\Media:/boil/media/tv -p 5000:5000 -d manager:latest