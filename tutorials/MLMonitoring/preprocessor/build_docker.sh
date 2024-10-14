#!/bin/bash

docker build -t rdsea/obj_proc_qoa:teaching -f ./Dockerfile .
docker rmi -f $(docker images -q --filter "dangling=true")
docker push rdsea/obj_proc_qoa:teaching