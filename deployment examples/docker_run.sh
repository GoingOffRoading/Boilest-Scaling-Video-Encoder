#!/bin/sh

# Run manager container
docker run --user=appuser --env=Role=Manager --volume=C:\Users\cwest\btest:/app -p 5000:5000 -d  manager:latest
