# ML Serving tutorial

## Study goal
The purpose of this tutorial is to understand Machine Learning (ML) serving, create a simple end-to-end ML pipeline in Python and deploy it on [Kubernetes](https://kubernetes.io/)(K8s) environment. This covers all  basic steps making a serving pipeline including preparing data, develop ML application as microservices, deploy ML as a Service (MLaaS) on K8s environment. Thereby, we can scale application, re-train or replace the model on run time without interrupting the ML service.

Kubernetes is an open-source for automating deployment, allowing us deploy containerized applications on top of several container runtimes, for example: Docker, containerd, CRI-O. With Kubernetes, we can deploy scalable, elastic, and reliable ML pipelines without much human effort. Here, we practice ML serving by building your own ML application, containerizing the application and deploying it to a pre-setup K8s server on Google Cloud. Thereafter, we have to re-configure the application to serve multi-tenants as well as scale the ML service.

It is recommended that you use linux environment.

## Prerequisite
* [Docker](https://docs.docker.com/get-docker/), [Kubernetes](https://kubernetes.io/) or [Minikube](https://minikube.sigs.k8s.io/docs/)

## Machine Learning Models under Testing
Within this tutorial, we will practice with an ML application that detects some common objects in submitted images. The model uses [Darknet](https://pjreddie.com/darknet/) which implements [YOLOv3](https://arxiv.org/abs/1804.02767) as the core neural network.

The [model implementation](https://github.com/pjreddie/darknet) provides Python interfaces while most parts are written in C and Cuda so that we can deploy it on diverse hardware architectures. 

The images for this experiment are extracted from the Google Open Image dataset [(V6 - released Feb. 2020)](https://storage.googleapis.com/openimages/web/index.html), containing approximately 9 million images of varying sizes (from 40KB to 1MB) and qualities in over 600 object classes.


<p align = "center">
<img src = "./client/image/bird.jpg" width=50% height=50%>
</p> 
<p align = "center">
Figure 1: Sample image (from Google Open Image)
</p>


<p align = "center">
<img src = "./client/image/bird_label.jpg" width=50% height=50%>
</p>
<p align = "center">
Figure 2: Labeled image (from Google Open Image)
</p>

The sample response:

```
Response: b'{"data": [["bird", 0.9479365348815918, [375.28814697265625, 469.7745666503906, 563.1881103515625, 436.5980529785156]]], "uid": "f5abecdafccf402580054d28b13672fa", "success": "true"}'
```


## Deploying ML Service on your own machine

### Question:
- After developing an ML pipeline, how could you deploy the pipeline on heterogeneous computing resources?
- How to automate environment deployments (hardware/software dependencies) for all services within the pipeline with minimal manual efforts.
- What would you do if the workload increase/decrease suddently? 
- How could you guarantee the serving quality?
- What would you optimize when serving (multiple) ML services?

### Practice
* Clone this git (https://github.com/rdsea/sys4bigml/) if you have not done so
* Move to the tutorial folder `tutorials/MLServing-2022`

### Build a containerized application

There are 3 separate folders for 3 microservices: Web service, Preprocessing service and Inference service.
Each folder contains a Python application, a Dockerfile, and a requirement file (dependencies)
* In this tutorial, we use docker to build a container for our ML service:
    - The `Dockerfile` provides step by step to build our desired image from `python:3.9` based image running on `amd64` architecture (depending on where you will run the container, you can change the based image that fit the hardware architecture).
* Build the docker image by running `build_docker.sh` (You may need to change the file permission using `chmod`, but you should run it line by line in your terminal to understand the process and easier to handle some unexpected errors):
    * Change the name tag and version of the image you're going to build:
```bash
$ docker build -t <your_repo>/<image_name>:<version> -f ./Dockerfile .
```

* Archive the recently built image and import it to K8s system.
```bash
# Archive docker image (using the name tag changed above) 
$ docker save <your_repo>/<image_name> > <archive_name>.tar

# Load image to k8s system
$ minikube image load <archive_name>.tar

# List all image available
$ minikube images ls
```

***Note***: You can use microk8s instead of minikube (refer to [another tutorial](https://version.aalto.fi/gitlab/sys4bigml/cs-e4660/-/tree/master/tutorials/MLServing-2021-discontinued))
You can also build your docker image locally then push it into [Dockerhub](https://hub.docker.com/) so that you don't have to import the image to K8s as it automatically finds the image from Dockerhub if it's not available at local.

## K8s Deployment
* The simple deployments of all microservices in K8s are provided in `deployment/<filename>.yaml`. Inside the deployment file, we should specify the name of the deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <deployment-name>
  labels:
    app: <app-name>
```
* We also have to specify the desired image so that K8s can start a container using the image that we build above (use the name tag that you use in the previous step).
```yaml
spec:
    containers:
    - image: <your_repo>/<image_name>:<version>
    name: ml
```
* Start the deployment using the following command:
```bash
$ minikube kubectl apply -f <path_to_deployment_file>
```

Now we can check if the deployment started

```bash
    $ minikube kubectl get all
```
Returned result
```
NAME                                 READY   STATUS    RESTARTS   AGE
pod/edge-web-server-77df7888fd-wr2wg   1/1     Running   11         4d

NAME                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.152.183.1   <none>        443/TCP   6d1h

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/edge-web-server   1/1     1            1           4d

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/edge-web-server-77df7888fd   1         1         1       4d
```
You can see the status is "Running" and the READY tab is "1/1" so that it has been started successfully.
If it not show as above, you can export the logs by the following command for debugging:

```bash
$ minikube kubectl logs <instance_name>
```
## **Send ML Request from Client Application**
We provide a simple client application within the `client` folder. You can just simply run the python application by the following command:
```bash
$ python3 client.py
```
The client application will send a random image from `client/image` folder to the web server that you just start.

***Note***: modify the IP address before running. If there is a problem with the network (web service is unable to reach) you can try to deploy the client in K8s, access the bash shell of the client deployment then run it with the similar command above.

The terminal should return the prediction result as below:

```bash
Response: b'{"data": [["bird", 0.9479365348815918, [375.28814697265625, 469.7745666503906, 563.1881103515625, 436.5980529785156]]], "uid": "f5abecdafccf402580054d28b13672fa", "success": "true"}'
```

## Practice
- Change the ML serving model (e.g., using YOLOv2) without causing interruption (Hint: develop new models, modify the model information, build a new image, and redeploy the service). 

## Open questions
- What if an ML model requires a lot of resources? Are using Flask and Docker and calling the inference as a blocking function suitable?
- What is the role of observability for Elastic ML serving? Can you setup an observability system for this ML serving example?
- How do we know the current model is outdated then when we should update the serving model or deploy the new one?
- Should we deploy multiple models for one service (e.g: different requests might be served by different models)?
- What would happen if any service container is down? how to backup and recover?


## References
The tutorial is built upon Kubernetes documents. The main references is:

* https://kubernetes.io/
* https://hub.docker.com/

## Contributions

Author:   Minh-Tri Nguyen, (tri.m.nguyen@aalto.fi)
Editor:   Linh Truong
