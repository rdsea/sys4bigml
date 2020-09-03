# ML Serving tutorial

## Study goal
The purpose of this tutorial is to create cluster providing Machine Learning (ML) as a service using [PredicitonIO](https://predictionio.apache.org/). This will consist of how to collect and prepare data, develop, train and deploy your ML model. Given many useful APIs, we can not only import existing data but also send data to server using light weight client application. After model is training, it can be deployed and replace the old model on run time without interuping ML service.

Apache PredictionIO is an open source ML Server for developers and data scientists to create predictive engines solving many ML tasks. It lets developer:[[1]](https://predictionio.apache.org/)

- Quickly build and deploy an engine as a web service on production with customizable templates;
- Respond to dynamic queries in real-time once deployed as a web service;
- Evaluate and tune multiple engine variants systematically;
- Unify data from multiple platforms in batch or in real-time for comprehensive predictive analytics;
- Speed up ML modeling with systematic processes and pre-built evaluation measures;
- Support ML and data processing libraries such as Spark MLLib and OpenNLP;
- Implement your own ML models and seamlessly incorporate them into your engine;
- Simplify data infrastructure management.

In this tutorial, we only practice basic functionalities of PredictionIO including creating simple ML cluster, colllecting data, developing and providing ML service. Further, this tutorial gives you some references where you can learn how to evaluate and tuning your model.
It is recommended that you use linux environment.

## Accompanying Slides and Video
* [Slides](ml_serving_2020.pdf)
* A hands-on video as part of this tutorial

## Installation
You can download and install Docker from [here](https://www.docker.com/get-started)

Clone Docker-PredictionIO in the [git repository](https://github.com/apache/predictionio/tree/develop/docker).

```bash
    $ git clone https://github.com/apache/predictionio.git
```
Move to the directory including Dockerfile

```bash
    $ cd predictionio/docker
```
Build Dockerfile
```bash
    $ docker build -t predictionio/pio pio
```

As we are using docker to deploy PredictionIO service, the command tool `pio-docker` is used instead of `pio`
```bash
    $ export PATH=`pwd`/bin:$PATH
```
## Setup Server cluster
At this point, we start a cluster including a predictionIO server, a spark master, a spark worker and an elasticsearch service.

```bash
    $ docker-compose -f docker-compose.yml \
      -f docker-compose.spark.yml \
      -f elasticsearch/docker-compose.base.yml \
      -f elasticsearch/docker-compose.meta.yml \
      -f elasticsearch/docker-compose.event.yml \
      -f localfs/docker-compose.model.yml \
      up
```

After pulling the images, the script will start Elasticsearch, Apache PredictionIO, and Apache Spark. The event server should be ready at port 7070, and you should see these logs in the command line interface.
```
    ...
    pio_1       | [INFO] [Management$] Your system is all ready to go.
    pio_1       | [INFO] [Management$] Creating Event Server at 0.0.0.0:7070
    pio_1       | [INFO] [HttpListener] Bound to /0.0.0.0:7070
    pio_1       | [INFO] [EventServerActor] Bound received. EventServer is ready.
```

Now we can check the server status using `pio-docker`
```bash
    $ pio-docker status
```
Returned result
```
    [INFO] [Management$] Inspecting PredictionIO...
    [INFO] [Management$] PredictionIO 0.13.0 is installed at /usr/share/predictionio 
    [INFO] [Management$] Inspecting Apache Spark...
    [INFO] [Management$] Apache Spark is installed at /usr/share/spark-2.2.3-bin-hadoop2.7
    [INFO] [Management$] Apache Spark 2.2.3 detected (meets minimum requirement of 1.6.3)
    [INFO] [Management$] Inspecting storage backend connections...
    [INFO] [Storage$] Verifying Meta Data Backend (Source: ELASTICSEARCH)...
    [INFO] [Storage$] Verifying Model Data Backend (Source: LOCALFS)...
    [INFO] [Storage$] Verifying Event Data Backend (Source: ELASTICSEARCH)...
    [INFO] [Storage$] Test writing to Event Store (App Id 0)...
    [INFO] [Management$] Your system is all ready to go.
```

Make sure your cluster is up:
```bash
    $ docker ps
```
```
    CONTAINER ID        IMAGE                                                 COMMAND                  CREATED             STATUS              PORTS                                                                    NAMES
    e989883b63e9        bde2020/spark-worker:2.2.2-hadoop2.7                  "/bin/bash /worker.sh"   2 weeks ago         Up 40 seconds       0.0.0.0:8081->8081/tcp                                                   spark-worker-1
    ef824e448270        predictionio/pio:latest                               "sh /usr/bin/pio_run"    2 weeks ago         Up 40 seconds       0.0.0.0:7070->7070/tcp, 0.0.0.0:8000->8000/tcp, 0.0.0.0:8080->8080/tcp   docker_pio_1
    e2257ec95006        bde2020/spark-master:2.2.2-hadoop2.7                  "/bin/bash /master.sh"   2 weeks ago         Up 41 seconds       6066/tcp, 0.0.0.0:7077->7077/tcp, 0.0.0.0:8090->8080/tcp                 spark-master
    f6d312588d29        docker.elastic.co/elasticsearch/elasticsearch:5.6.4   "/bin/bash bin/es-do…"   3 months ago        Up 41 seconds       9200/tcp, 9300/tcp                                                       docker_elasticsearch_1
```

You may want to run other options which are described at: <https://github.com/apache/predictionio/blob/develop/docker/README.md#run-predictionio-with-selectable-docker-compose-files>.

Or you may want to expose some service from your virtual cluster to your real machine for monitoring, you can modify the dockerfiles

For example:
```yml
    services:
      spark-master:
        image: bde2020/spark-master:2.2.2-hadoop2.7
        container_name: spark-master
        ports:
          - "8090:8080"
          - "7077:7077"
```

Now your Server is ready to deploy ML application

### Deploy a simple application
- Declare you application: All application must be register before deploying on server.

```bash
    $ pio-docker new app YOUR_APPLICATION_NAME
```
Example result with application name: demo_recommendation
```
    [INFO] [App$] Initialized Event Store for this app ID: 2.
    [INFO] [App$] Created new app:
    [INFO] [App$]       Name: demo_recommendation
    [INFO] [App$]         ID: 2
    [INFO] [App$] Access Key: ayA5BT7mhFLsAokkIEu5TBvVHhPnK_CDhAjXTXMmDoWf8YmYk4gPUmzm31Ix9rBY
```
Server will return application `ID` and the `Access Key` which are used to specify your application while collecting data as well as providing ML service.

You can also check your application list:
```bash
    $ pio-docker app list
```
```
    [INFO] [Pio$]                 Name |   ID |                                                       Access Key | Allowed Event(s)
    [INFO] [Pio$]                LRapp |    1 | 3vQpvZ4NX6AGSve59HyG7ohz3JaddMW6n39yKfI-ErhC_r7PY_Sor_MT8LvZxtnA | (all)
    [INFO] [Pio$]  demo_recommendation |    2 | ayA5BT7mhFLsAokkIEu5TBvVHhPnK_CDhAjXTXMmDoWf8YmYk4gPUmzm31Ix9rBY | (all)
    [INFO] [Pio$] Finished listing 2 app(s).
```

- Clone the example code: we prepare an example code from existing template. [Here](http://predictionio.apache.org/gallery/template-gallery/), you can find more useful templates and instructions.
```bash
    $ git clone OUR_GIT_REPO_FOR_EXAMPLE
    $ cd demo_recommendation
```

Inside the `demo_recommendation` directory, you can find the ML model is implemented in `src` folder while other things are to help you build and deloy right the way.
The `source code` is implemented in Scala and it's using `predictionio` library to utilize pre-modified ML algorithms. You may have to install `predictionio` using `pip`.
```bash
    $ pip install predictionio
```

Under the directory, you should find an engine.json file; this is where you specify parameters for the model. You have to modify the appname the same as the one you registered on your server.

```json
      ...
      "datasource": {
        "params" : {
          "appName": "demo_recommendation"
        }
      },
  ...
```
- Import existing data to your server

We are using a sample data in an open dataset called [`movielens`](https://grouplens.org/datasets/movielens/). The data is already at `data/sample_movielens_data.txt`.

To import data, you may want to use some supported [APIs](http://predictionio.apache.org/datacollection/eventapi/). Here, a python application is provided in `import_eventserver.py`.

```bash
    $ python data/import_eventserver.py --access_key $ACCESS_KEY
```
At the end, you should see the following output:

```
    Importing data...
    1000 events are imported.
```

- Build your model

Start with building your Model. Run the following command
```bash
    $ pio-docker build --verbose
```

Upon successful build, you should see a console message similar to the following.
```
    [INFO] [Console$] Your engine is ready for training.
```

- Train your model
```bash
    $ pio-docker train
```
When your model is trained successfully, you should see a console message similar to the following.

```
    [INFO] [CoreWorkflow$] Training completed successfully.
```

- Deploy your model

The model is now ready to deploy, run:
```bash
    $ pio-docker deploy
```

When the model is deployed successfully and running, you should see a console message similar to the following:
```
    [INFO] [HttpListener] Bound to /0.0.0.0:8000
    [INFO] [MasterActor] Engine is deployed and running. Engine API is live at http://0.0.0.0:8000.
```

By default, the deployed model binds to <http://localhost:8000>. You can visit that page in your web browser to check its status.

![localhost](model_server.png)

- Make recommendation 

There are some APIs that you can use to send a request for making prediction. Here, an example in python is prepared at `send_query.py`
```bash
    $ python ./data/send_query.py
```

Server will return the result similar to the following output:
```
    {u'itemScores': [{u'item': u'35', u'score': 7.27783848861931}, {u'item': u'53', u'score': 5.982870529518669}, {u'item': u'69', u'score': 5.716560737619193}, {u'item': u'23', u'score': 5.387127686924485}]}<type 'dict'>
```

- Streaming data

Since the server is running, you can send data to it in real-time using the same APIs mentioned before.

An example is repared in `stream_eventserver.py`, and the data for streaming is in `stream_movielens_data.txt`

```bash
    $ python ./data/stream_eventserver.py
```

You should see the following output:

```
    Namespace(access_key='ayA5BT7mhFLsAokkIEu5TBvVHhPnK_CDhAjXTXMmDoWf8YmYk4gPUmzm31Ix9rBY', file='./data/stream_movielens_data.txt', url='http://localhost:7070')
    Sending data...
    Sent data: 0
    Sent data: 1
    Sent data: 2
    Sent data: 3
    ...
```

Since then, you can update, re-train and deploy new model by repeating above steps while the previous vertion is still running.

## Issues you may encounter during the tutorial
- Docker build problem due to broken maven repo

Replace the link by: <https://repo1.maven.org/maven2/org/postgresql/postgresql/$PGSQL_VERSION/postgresql-$PGSQL_VERSION.jar>

- Broken link for sbt-launcher while traing ML model

Access the predictionIO server using `docker exec`
```bash
    $ docker exec -it name_container /bin/bash
```
Download then place the sbt-launcher at the required directory (don't forget to rename the downloaded file) using `wget`

For example:
```bash
    $ wget https://repo1.maven.org/maven2/org/scala-sbt/sbt-launch/1.2.8/sbt-launch-1.2.8.jar
```


## References
The tutorial is built upon PredictionIO documents. The main references is:

* http://predictionio.apache.org/templates/recommendation/quickstart/
