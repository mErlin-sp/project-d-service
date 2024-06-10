#!/usr/bin/env bash
docker run -P -d \
    --env MYSQL_ROOT_PASSWORD=qwertyuiop \
    --env MYSQL_DATABASE=project-d-db \
    --name project-d-db \
    --restart always \
    --network host \
    mysql:8.4
