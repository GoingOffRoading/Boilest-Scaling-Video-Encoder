#!/bin/sh

# Run manager container

docker run --env=Role=Manager --volume=C:\Users\cwest\btest:/Boil/App --volume=C:\Media:/Boil/Media/TV -p 5000:5000 -d boilest:latest
docker run --volume=C:\Media:/Boil/Media/TV -d boilest:latest