#!/bin/bash


container_id=$(docker run -dit \
-v /mnt/wind/Games/minecraft1.12.1-all/server/:/work \
-w /work -e MEM_min="512" -e MEM_max="1024" -e MC_SERVER="minecraft_server.1.12.1.jar" \
-p 25565:25565/tcp \
calllivecn/mc_server:v1)
docker logs -f $container_id
