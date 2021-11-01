#!/bin/bash

# Change name tag before runing
docker build -t <your_repo>/<image_name>:<version> -f ./Dockerfile .

# Remove dangling image
docker rmi $(docker images -q --filter "dangling=true")

# Archive docker image (using the name tag changed above) 
docker save <your_repo>/<image_name> > <archive_name>.tar

# Import image to k8s system
microk8s ctr image import <archive_name>.tar

# List all image avialable
# microk8s ctr images ls