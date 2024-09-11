#!/bin/bash

docker build -t rdsea/obj_client_qoa:teaching -f ./Dockerfile .
docker rmi -f $(docker images -q --filter "dangling=true")
