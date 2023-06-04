# ML Serving tutorial

>Note that the tutorial is possible working but we have stopped to update it. 

## Study goal
The purpose of this tutorial is to create a simple end-to-end pipeline providing Machine Learning (ML) service using Python and [Kubernetes](https://kubernetes.io/)(K8s). This covers all  basic steps making a serving pipeline including preparing data, developing, training ML model, and deploying ML models on K8s server. After deploying models, we can re-train or replace the model on run time without interrupting the ML service.

Kubernetes is an open-source for automating deployment, allowing us deploy containerized applications on top of several container runtimes, for example: Docker, containerd, CRI-O. With Kubernetes, we can deploy scalable, elastic, and reliable ML pipelines without much human effort. Here, we practice ML serving by building your own ML application, containerizing the application and deploying it to a pre-setup K8s server on Google Cloud. Thereafter, we have to re-configure the application to serve multi-tenants as well as scale the ML service.


It is recommended that you use linux environment.

## Accompanying Slides and Video
* [Slides](ml_serving_2020.pdf)
* [A hands-on video as part of this tutorial](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=e93364e2-b7fb-4d17-a98f-ac3d00f3c95c)

## Prerequisite

* [Paho-Mqtt](https://pypi.org/project/paho-mqtt/), [Pandas](https://pandas.pydata.org/), [numpy](https://numpy.org/)
* [TensorFlow](https://www.tensorflow.org/install), [TensorFlow Lite Runtime](https://www.tensorflow.org/lite/guide/python)
* [Docker](https://docs.docker.com/get-docker/), [Kubernetes](https://kubernetes.io/) or [MicroK8s](https://microk8s.io/)

## **ML Model & Data**
## Machine Learning Models under Testing
Within this tutorial, we introduce 2 ML [models](ml_model/) which predict the future values of a single time series based on historical data. The first model uses [LSTM](https://en.wikipedia.org/wiki/Long_short-term_memory) as the core neural network while the other only adopt a simple [fully-connected ANN](https://en.wikipedia.org/wiki/Artificial_neural_network)

Both models are implemented in TensorFlow and converted into tflite so that we can deploy them on diverse hardware architectures. 

The models currently predict the Load Power Grid on a sample data [BTS dataset](https://github.com/rdsea/bigdataplatforms/tree/master/data/bts) introduced in [Big Data Platforms - CS-E4640](https://github.com/rdsea/bigdataplatforms/). 

Sample data:
| index | station_id | parameter_id | reading_time | value |
|-------|---------|------------|--------------|----------|
| 0     | 1161114002 | 122          | 1487441883 | 221   |  
| 1     | 1161114002 | 122          | 1487442194 | 223   | 
| 2     | 1161114002 | 122          | 1487442922 | 186   | 
| 3     | 1161114002 | 122          | 1487442929 | 120   | 
| 4     | 1161114002 | 122          | 1487442933 | 53   | 

The normalized data sample:
| index | station_id | parameter_id | reading_time | value |
|-------|---------|------------|--------------|----------|
| 0     | 1161114002 | 122          | -11.891749028408888 | -0.31175913823410106   |  
| 1     | 1161114002 | 122          | -11.891471250631112 | -0.23459683598503628   | 
| 2     | 1161114002 | 122          | -11.891193472853333 | -0.08027223148690674   | 
| 3     | 1161114002 | 122          | -11.890915695075556 | -0.003109929237841972   | 
| 4     | 1161114002 | 122          | -11.889249028408889 | 0.07405237301122279   | 


Note: Inside the sample test, the `reading_time` has been converted to Unix timestamp.

## **ML Service**
In this tutorial, all the ML requests/responses are sent via an MQTT Broker deployed on cloud.
## Training ML model
* The ML model is prepared in the folder `ml_training`. You can simply run it using python 3 and the prerequisite libaries mentioned above.
* To change the model, modify the source code between the commented lines inside `model.py` and train the model again.

Note: Make sure the dimensions of input and output of the model is unchanged.
* After training, the model is saved in 2 formats (Tensor and tflite-runtime). You can change the file path and use it to load the model in the later experiments.
## ML application
* The ML application is defined in `server_app.py`, it simply reads the configuration from `server.json` and starts an instance for serving ML request from clients

* Inside `server.json`, you can modify the user id, broker service, the message queue, and the model information, which will be used for loading the ML model or connecting to MQTT broker.

***Note***: you have to specify your own in/out queue names so that your application send request and receive response from different queues from other students.


## Deploying ML Service on cloud
* First, connect to server using ssh with provided username and password:

```bash
$ ssh <username>@<serverip>
```
* Copy the source code to server if you want to push the folder from your local machine
```bash
$ scp -r <path_to_your_source_code> <username>@<serverip>:/home/<username>
```
* Or clone the folder from git
```bash
$ git clone https://version.aalto.fi/gitlab/sys4bigml/cs-e4660.git
```

### Build a containerized application
* Take a look at the `server/server.py` and other related `class` to understand how to load the model from exported file.
* The python application is prepared in `server/server_app.py` with the pre-configuration saved in `server/server.json`
* In this turorial, we use docker to build a container for our ML service:
    - The `Dockerfile` provides step by step to build our desired image from an Ubuntu core running on `amd64` architecture. That requires pre-download the `ubuntu-groovy-core-cloudimg-amd64-root.tar.gz` and save it in `unbuntu_image` folder. You can find the image [here](https://partner-images.canonical.com/core/groovy/current/ubuntu-groovy-core-cloudimg-amd64-root.tar.gz)
* Build the docker image by running `build.sh` (You may need to change the file permission using `chmod`, but you should run line by line in your terminal to understand the process and easier to handle some unexpected errors):
    * Change the name tag and version of the image you're going to build:
```bash
$ docker build -t <your_repo>/<image_name>:<version> -f ./Dockerfile .
```

* Archive the recently built image and import it to K8s system (read `build.sh` for more details).

***Note***: You can download the ubuntu image on remote server using `wget` or use other images but you have to change the file name and file path in `Dockerfile`
```bash
$ wget <image_link>
``` 
```dockerfile
ADD ./ubuntu_image/ubuntu-groovy-core-cloudimg-amd64-root.tar.gz /
```
You can also build your docker image locally then push it into [Dockerhub](https://hub.docker.com/) so that you don't have to import the image to K8s as it automatically find the image from Dockerhub if it's not available at local.

## K8s Deployment
* A simple deployment of K8s is provided in `deployment/ml_deployment.yaml`. Inside the deployment file, we should specify the name of the deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-deployment
  labels:
    app: ml
```
* We also have to specify the desired image so that K8s cand start a container using the image that we build above (use the name tag that you use in the previous step).
```yaml
spec:
    containers:
    - image: <your_repo>/<image_name>:<version>
    name: ml
```
* Start the deployment using the following command:
```bash
$ microk8s kubectl apply -f <path_to_deployment_file>
```

Now we can check if the deployment started

```bash
    $ microk8s kubectl get all
```
Returned result
```
NAME                                 READY   STATUS    RESTARTS   AGE
pod/ml-deployment-77df7888fd-wr2wg   1/1     Running   11         4d

NAME                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.152.183.1   <none>        443/TCP   6d1h

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ml-deployment   1/1     1            1           4d

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/ml-deployment-77df7888fd   1         1         1       4d
```
You can see the status is "Running" and the READY tab is "1/1" so that it has been started successfully.
If it not show as above, you can export the logs by the following command for debugging:

```bash
$ microk8s kubectl logs <instance_name>
```
## **Send ML Request from Client Application**
We provide a simple client application within the `client` folder. You can just simply run the python application by the following command:
```bash
$ python3 client_app.py
```
The client application will automatically read the configuration file (`client.json`) then init a connection to MQTT broker to send ML request as well as receive the response. 

***Note***: specify the queue name as the previous step to make sure you send/receive messages to/from the right queues

The terminal should return the prediction result as below:
```bash
Data sent
message topic= outqueue/lstm
Returned Results: {"LSTM": -0.13547556102275848}
Data sent
message topic= outqueue/lstm
Returned Results: {"LSTM": -0.22059251368045807}
```

## Your Excercise
- Change the ML serving model without causing interuption (Hint: develop new model, modify the model information, build a new image, and re-deploy the service). 
- The current ML application only serve single tenant, your responsibility is to make it serve multi-tenants. You can run multiple client applications from multiple terminal windows with differents configurations (client.json). Also, you have to scale the deployment up and down based on the workload. (Hint: modify the server, client application, mqtt client, and deployment profile (yaml file)).

## Open questions

- What is the role of observability for Elastic ML serving? Can you setup an observability system for this ML serving example?
- How do we know the current model is outdated then when we should update the serving model or deploy the new one?
- Should we deploy multiple models for one service (e.g: different requests might be served by different models)?
- What would happen if any service container is down? how to backup and recover?


## References
The tutorial is built upon Kubernetes documents. The main references is:

* https://microk8s.io/
* https://kubernetes.io/
* https://hub.docker.com/

## Contributions

Author:   Minh-Tri Nguyen, (tri.m.nguyen@aalto.fi)
Editor:   Linh Truong
