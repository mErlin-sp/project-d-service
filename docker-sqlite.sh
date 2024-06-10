#!/usr/bin/env bash
docker build -t project-d-service .
docker run -P -d \
    --name project-d-service \
    --env DB_TYPE=SQLITE \
    --network host \
    --restart always \
    project-d-service
