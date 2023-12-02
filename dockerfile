FROM alpine
RUN apk add --no-cache python3 py3-pip ffmpeg sqlite bash tzdata
RUN pip install --no-cache-dir --root-user-action=ignore celery flower requests Flask

ENV TZ=US/Pacific

RUN apk update
RUN apk upgrade

# Need to set UID/GID since we're likely interfacing with files owned by a non-root user
ARG UID=1000
ARG GID=1000

RUN mkdir -p /boil_hold
RUN mkdir -p /Boilest
RUN mkdir -p /Scripts

RUN mkdir -p /media
RUN mkdir -p /anime
RUN mkdir -p /tv
RUN mkdir -p /movies

COPY /Scripts /Scripts
#COPY /Scripts/DB /Boilest/DB
WORKDIR "/Scripts"

# Used in Celery.sh
ENV Manager No

# User in Flower: https://flower.readthedocs.io/en/latest/config.html
ENV FLOWER_FLOWER_BASIC_AUTH celery:celery
ENV FLOWER_persistent true
ENV FLOWER_db /Boilest/flower_db
ENV FLOWER_purge_offline_workers 60
ENV FLOWER_UNAUTHENTICATED_API true

# Used in celery and rabbitmq
ENV user celery
ENV password celery
ENV celery_host 192.168.1.110
ENV celery_port 31672
ENV celery_vhost celery
ENV rabbitmq_host 192.168.1.110
ENV rabbitmq_port 32311

# USed in FFmpeg
ENV ffmpeg_settings "-hide_banner -loglevel 16 -stats -stats_period 10"


# Add a user that is the same user group as the data being read
# Is this clean?  Not really...  Will need to revisit this later

RUN addgroup -g 1000 boil 
RUN adduser -D boil -G boil -u 1000
RUN chown -R boil:boil /boil_hold /Scripts /Boilest

#RUN chmod +x /Scripts/Celery.sh /Scripts/container_start.py

USER boil

EXPOSE 5000
EXPOSE 5555

ENTRYPOINT ["/bin/sh"]
CMD ["/Scripts/Celery.sh"]


