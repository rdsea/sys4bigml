#!/bin/bash

docker build -t rdsea/obj_web:teaching_qoa -f ./Dockerfile .
docker rmi -f $(docker images -q --filter "dangling=true")