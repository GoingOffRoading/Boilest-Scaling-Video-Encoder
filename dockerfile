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
#RUN mkdir -p /Boilest
#RUN mkdir -p /Boilest/DB
#RUN mkdir -p /Boilest/Configurations
RUN mkdir -p /Scripts

RUN mkdir -p /Media
RUN mkdir -p /Anime_TV
RUN mkdir -p /Aime_Movies
RUN mkdir -p /Live_Action_TV
RUN mkdir -p /Live_Action_Movies
RUN mkdir -p /Animated_TV
RUN mkdir -p /Animated_Movies

COPY /Scripts /Scripts
#COPY /Scripts/DB /Boilest/DB
WORKDIR "/Scripts"

# Used in Celery.sh
ENV Manager No
ENV Worker Yes

# User in Flower: https://flower.readthedocs.io/en/latest/config.html
ENV FLOWER_FLOWER_BASIC_AUTH celery:celery
ENV FLOWER_persistent true
ENV FLOWER_db /Boilest/flower_db
ENV FLOWER_purge_offline_workers 60
ENV FLOWER_UNAUTHENTICATED_API true

# Used in celery and rabbitmq
ENV Celery_User celery
ENV Celery_PW celery
ENV RabbitMQ_Server 192.168.1.110
ENV RabbitMQ_Port 31672

# Add a user that is the same user group as the data being read
# Is this clean?  Not really...  Will need to revisit this later

RUN addgroup -g 1000 boil 
RUN adduser -D boil -G boil -u 1000
RUN chown -R boil:boil /boil_hold /Scripts /Boilest
USER boil

EXPOSE 5000
EXPOSE 5555

ENTRYPOINT [ "/bin/sh"]
CMD ["/Scripts/Celery.sh"]