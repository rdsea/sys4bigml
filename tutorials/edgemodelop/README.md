# Building an edge ML pipeline
**To be updated**

The goal of this tutorial is to build a simple ML system in the edge. The system will combine two pipelines: IoT streaming data pipeline and ML serving pipeline.

## Overview of the edge ML system

The system will include two sub parts:
* IoT streaming data pipeline: in this pipeline, sensors monitor environments  and send monitoring data to an edge IoT Data Hub. From the IoT Data Hub, lightweight ingestion services will take data and push to other components.
  - sensors: will be emulated by python programs reading real IoT data from files
  - IoT Data Hub: will be implemented by a simple MQTT brokers
  - Ingestion services: will be implemented as Python/Javascript
  - The whole IoT Streaming data pipeline will be run atop edge devices, such as Raspberry PI
* Edge ML serving: in this pipeline, ML models are deployed in an edge ML serving platform and perform inferences
  - ML Serving platform: will use TensorFlowX

## Developing ML models in the cloud and transform the model to the edge

### ML Models in Conventional Environment
We will practice the development of ML models in conventional environments. See [previous tutorials on ML serving] for further information. In this tutorial we have existing models developed with TensorFlows
* Model 1: [TBD]
* Model 2: [TBD]

### Transforming conventional models to edge environment

Step to export conventional models to edge models:



## References
* https://docs.openvinotoolkit.org/2020.4/openvino_docs_MO_DG_Deep_Learning_Model_Optimizer_DevGuide.html
* https://raw.githubusercontent.com/tensorflow/serving/master/tensorflow_serving/example/mnist_saved_model.py

## Authors
