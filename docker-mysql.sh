#!/usr/bin/env bash
docker build -t project-d-service .
docker run -P -d \
    --name project-d-service \
    --env DB_TYPE=MYSQL \
    --env MYSQL_ADDR=127.0.0.1 \
    --env MYSQL_PASSWORD=qwertyuiop \
    --network host \
    --restart always \
    project-d-service
