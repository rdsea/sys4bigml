# Hands-on Machine Learning pipeline on Edge

## Learning objectives

The purpose of this tutorial is to build a simple dynamic inferencing system with Machine Learning serving on edge devices. The inferencing system will consist of 2 subsystems that are IoT data streaming data and ML pipeline.

In the first part, IoT data streaming, we have to face the variety of edge resources. We are going to use one of the most common messages delivery protocol, [MQTT](https://mqtt.org/) for transporting IoT data over TCP/IP. In the second part, an ML pipeline would be deployed partially on edge devices, which have limited resources but are located close to users, to make predictions in real-time. While the main process of data pre-processing and model training are still performed in a centralized manner on cloud, moving ML inference to the edge can mitigate the burden on cloud computing as well as network functions.

To complete this tutorial, you are recommended to use linux environment.

## Accompanying Slides and Video
* [Slides](cs-e4660-hands-on-edge_ml.pdf)

## Prerequisite
We assume that edge devices will be Raspberry PIs.
Given two Raspberry Pi 4, one would be installed with Unbuntu (64-bit) 20.04 (Ubuntu-Rasp), the other has the newest Raspberry Pi OS - Raspbian (32-bit) Released: 2020-08-20 (Raspbian-Rasp).
Since two different OSs would support different software stack and runtime environment, it partially demonstrates the variety of edge resources.

Raspberry Pi:
* [Python 3](https://www.python.org/download/releases/3.0/)
* [Python virtual env](https://docs.python.org/3/library/venv.html)
* [Java environment (Java 11 is recommended)](https://www.java.com/en)
* [Paho Mqtt](https://pypi.org/project/paho-mqtt/)
* [Numpy](https://numpy.org/)
* [TensorFlow Lite for specific hardware & OS](https://www.tensorflow.org/lite/guide/python)

Your computer (+all above):
* [Pandas](https://pandas.pydata.org/)
* [TensorFlow - 2.3.0](https://www.tensorflow.org/)
* [Matplotlib](https://matplotlib.org/)

Clone the source code to all devices and start python 3 virtual environment to make sure your application could run stably even when you update some dependencies.

## IoT Streaming data

In this section, we will build the simplest streaming pipeline for IoT using MQTT protocol provided by [HiveMQ](https://www.hivemq.com/). To have a well understanding of the HiveMQ Pub/Sub mechanism, you may prefer to [this](https://youtu.be/jTeJxQFD8Ak)

Here, our model includes two clients (one publisher and one subscriber) and one MQTT broker. The Raspbian-Rasp will play as a data collector and publish data to the MQTT broker running on the Ubuntu-Rasp, while your computer will be a subscriber which may save data to database for pre-processing or ML training later.

First, you need to implement an MQTT broker for receiving and forwarding messages. HiveMQ provides a community edition to help you build your own broker at the following [link](https://github.com/hivemq/hivemq-community-edition). *You should not use the public broker as this may lead to data leak.*

Note: *We have built many IoT data pipelines that you can reuse from [Big Data Platforms](https://version.aalto.fi/gitlab/bigdataplatforms/cs-e4640/-/tree/master/tutorials) and [IoTCloudSamples](https://github.com/rdsea/IoTCloudSamples)

After having an MQTT broker running on the Unbuntu-Rasp, we start initializing a subscriber on your computer. A python application is prepared in `mqtt/subcriber.py` to help you subscribe to the right topic and save data to an `CSV` file. Then, another application in `mqtt/publisher.py` will simulate a sensor collecting data then publish it to a pre-set topic (this app should be run on Raspbian-Rasp).

While running those applications, you may need to set the `ip address` and `port` of you MQTT broker using options `--host`, `--port` or data collecting interval using `--interval`


## Machine Learning Models under Testing
When data is ready, you can train our ML models locally on your computer. In this tutorial, we introduce 4 ML [models](https://version.aalto.fi/gitlab/sys4bigml/cs-e4660/-/tree/master/tutorials%2Fedgemodelop%2Fedge_client%2Fedge_machine_learning). Two of them are single and multiple variable linear regression, and two others are simple neural networks applying on single and multiple variables. Our neural networks consist of a normalizing layer, only one linear layer, and two ReLu layers for imitating non-linear correlation. Both neural networks are fully connected with the hidden size is 64. All mentioned models are used to predict the time that the next alarm happens at the specific station based on the previous alarm events.

Our models currently are applied to a sample data [BTS dataset](https://version.aalto.fi/gitlab/bigdataplatforms/cs-e4640/-/tree/master/data%2Fbts) introduced in [Big Data Platforms - CS-E4640](https://version.aalto.fi/gitlab/bigdataplatforms/cs-e4640).

Sample data:
| index | old_idx | station_id | datapoint_id | alarm_id | event_time | value | valueThreshold | isActive |
|-------|---------|------------|--------------|----------|------------|-------|----------------|----------|
| 0     | 983     | 1160629000 | 121          | 308      | 1487441883 | 231   | 230            | TRUE     |
| 1     | 984     | 1160629000 | 121          | 308      | 1487442194 | 231   | 230            | TRUE     |
| 2     | 985     | 1160629000 | 121          | 308      | 1487442922 | 231   | 230            | TRUE     |
| 3     | 986     | 1160629000 | 121          | 308      | 1487442929 | 231   | 230            | TRUE     |
| 4     | 987     | 1160629000 | 121          | 308      | 1487442933 | 231   | 230            | TRUE     |

As we're trying to predict the next alarm event for a specific alarm at one station, basically, we only use `index` and `event_time` for our experiments.

Note: Inside the sample test, the `event_time` has been converted to Unix timestamp.

Here, all model is ready in `edge_machine_learning` folder. You should train, test, or modify them one by one to see the differences. You can even customize your own model, uncomment some parts of our source to plot the results, compare the accuracy or runtime with others.

After running our application, the trained models will be saved at `exported_models` for deploying on other machines which support TensorFlow (2.3.0). For edge devices which do not support TensorFlow full version, those models is converted to TensorFlow Lite form located at `exported_model/tflite_model`.

## Machine Learning Serving on Edge
To serve Machine Learning on our edge devices, you need to copy the `exported_models` folder to our devices. The application in `response_request.py` start our ML serving on edge device and waiting for request.

Now we can easily simulate an user application to send request to our edge device using MQTT protocol (`send_request.py`).

## Open question for studies
* How can you measure the quality of ML service and system performance on the edge?
* How would you detect the quality of data that can influence the serving at near-real time?
* Can you identify a scenario for backup and restore service when failure occur on edge?
* Proposed a scenario for elastic, dynamic, collaborative, resource specific, multiple ML applications serving on edge cluster?

## References
* https://docs.openvinotoolkit.org/2020.4/openvino_docs_MO_DG_Deep_Learning_Model_Optimizer_DevGuide.html
## Contributions

Author:   Minh-Tri Nguyen, (tri.m.nguyen@aalto.fi)
Editor:   Linh Truong
