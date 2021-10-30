#!/bin/bash

docker build -t minhtribk12/qoa_ubuntu:1.0 -f ./Dockerfile .
docker rmi $(docker images -q --filter "dangling=true")