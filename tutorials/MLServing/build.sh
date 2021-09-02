#!/bin/bash

# Change name tag before runing
docker build -t server/server_ml:1.0 -f ./Dockerfile .

# Remove dangling image
docker rmi $(docker images -q --filter "dangling=true")

# Archive docker image (using the name tag changed above) 
docker save server/server_ml > server_ml.tar

# Import image to k8s system
microk8s ctr image import server_ml.tar

# List all image avialable
# microk8s ctr images ls