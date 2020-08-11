# Special Course in Computer Science: Advanced Topics in Systems for Big Data and Machine Learning, Spring 2020

## Overview
This is a pre-version of the CS-E4660. The course is focused on advanced topics in big data and ML systems.

## Lectures
* [Robustness, Reliability, Resilience and Elasticity](slides/lecture1-design-v0.1.pdf): We will examine  how systems should support the design of big data/ML with  Robustness, Reliability, Resilience and Elasticity
* [Benchmarking, Monitoring, Data Validation](lecture2-analytics-v0.1.pdf): For Big Data/ML various techniques are needed for understanding and support R4E. We examine basic benchmarking, monitoring and data validation techniques
* [Coordination of Big Data/ML Tasks](slides/lecture3-framework-v0.1.pdf): We will discuss about coordination and the relationship with R3E in Big Data/ML systems, including pipeline coordination, model serving, and experiment management.
* [Machine Learning with Edge Systems](slides/lecture4-edgecloud-v0.1.1.pdf): We discuss key open issues of machine learning in edge systems from the software system viewpoint.

## Hands-on tutorials
* [Machine learning experiments management](../tutorials/MLProjectManagement/README.md)
* [Performance monitoring](../tutorials/PerformanceMonitoring/README.md)

## Other relevant materials:

* [Quality of Analytics as an Approach for Optimizing ML Systems - Initial Results and Roadmap](slides/truong-fcai-2020-v0.3.pdf)

## Student Projects and Demonstration

* Modeling Automation - From Human to Machine:
  - Git project: https://github.com/OmerAhmedKhan/CS-E4002-Project
  - [Demonstration Video](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=f3c7a157-fdd1-428d-91f8-ab98007e0805)

* Machine Learning for Trading data:
  - Git project: https://github.com/jonatanvm/s4ml-project
  - [Demonstration Video](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=98c8ac66-276b-4390-b647-ab98007bcef7)

* MLFlow Meditrinae
  - Git project: https://github.com/vdandenault/MLFlow_Meditrinae
  -[Demonstration Video](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=940e7362-a140-4108-9b58-abac00fa3363)

## Reading List
### Robustness, Reliability, Resilience and Elasticity
* [SysML: The New Frontier of Machine Learning Systems](https://arxiv.org/abs/1904.03257)
* [Data Validation for Machine Learning](https://mlsys.org/Conferences/2019/doc/2019/167.pdf)
* [Challenges in Enabling Quality of Analytics in the Cloud](https://users.aalto.fi/~truongh4/publications/2017/truong-jdiq-2017.pdf)
* [Measuring, Quantifying, and Predicting the Cost-Accuracy Tradeoff](https://research.aalto.fi/files/38801332/paper.pdf)
* https://ai.googleblog.com/2019/12/improving-out-of-distribution-detection.html
* https://www.researchgate.net/publication/286584036_Principles_of_Software-Defined_Elastic_Systems_for_Big_Data_Analytics
* https://arxiv.org/pdf/1904.07204.pdf

### Benchmarking
* https://arxiv.org/pdf/1910.01500.pdf
* https://mlperf.org/training-overview
* https://aimatrix.ai/en-us/

###  QoA Tradeoffs analysis:
* https://www.microsoft.com/en-us/research/blog/reliability-in-reinforcement-learning/
* https://dzone.com/articles/qa-how-reliable-are-your-machine-learning-systems
* https://dl.acm.org/doi/10.1145/3352020.3352024

### Monitoring:
* https://www.sysml.cc/doc/2019/199.pdf
* https://monitorml.com/index.html
* https://dl.acm.org/doi/pdf/10.5555/1251203.1251209
* https://github.com/rdsea/bigdataincidentanalytics/tree/reasoning
* https://www.alibabacloud.com/blog/using-alibaba-cloud-tsdb-in-big-data-cluster-monitoring-scenarios_595164
* https://chromium.googlesource.com/external/github.com/tensorflow/tensorflow/+/r0.10/tensorflow/g3doc/tutorials/monitors/index.md

### Data Monitoring and Validation:
* https://mlsys.org/Conferences/2019/doc/2019/167.pdf
* https://github.com/tensorflow/data-validation
* https://towardsdatascience.com/hands-on-tensorflow-data-validation-61e552f123d7
* https://databricks.com/session/apache-spark-data-validation
* https://papers.nips.cc/paper/7947-a-simple-unified-framework-for-detecting-out-of-distribution-samples-and-adversarial-attacks.pdf
* https://cloud.google.com/blog/products/gcp/improving-data-quality-for-machine-learning-and-analytics-with-cloud-dataprep

### Orchestration and Pipelines
* https://dl.acm.org/doi/fullHtml/10.1145/3332301
* https://docs.microsoft.com/en-us/azure/machine-learning/concept-ml-pipelines
* https://shivaram.org/publications/keystoneml-icde17.pdf

### Reactive ML Systems
* Jeff Smith. 2018. Machine Learning Systems: Designs that scale (1st. ed.). Manning Publications Co., USA.https://www.manning.com/books/machine-learning-systems
### Serving with different models:
  * Prediction-Serving Systems, https://queue.acm.org/detail.cfm?id=3210557
  * Ryan Chard, Logan Ward, Zhuozhao Li, Yadu Babuji, Anna Woodard, Steven Tuecke, Kyle Chard, Ben Blaiszik, and Ian Foster. 2019. Publishing and Serving Machine Learning Models with DLHub. In Proceedings of the Practice and Experience in Advanced Research Computing on Rise of the Machines (learning) (PEARC ’19). Association for Computing Machinery, New York, NY, USA, Article 73, 1–7. DOI:https://doi.org/10.1145/3332186.3332246
  * https://cloud.google.com/ml-engine/docs/custom-prediction-routines
  * https://predictionio.apache.org/
  * https://github.com/EthicalML/awesome-production-machine-learning#model-deployment-and-orchestration-frameworks

### Edge ML

* https://www.usenix.org/system/files/conference/hotedge18/hotedge18-papers-talagala.pdf
* https://arxiv.org/pdf/1706.08420.pdf
* https://arxiv.org/pdf/1907.08349.pdf
* https://arxiv.org/pdf/1908.00080.pdf
* http://proceedings.mlr.press/v70/kumar17a.html
* https://www.ericsson.com/en/blog/2019/12/tinyml-as-a-service
* https://static.sched.com/hosted_files/osseu19/f9/elc2019-tinymlaas.pdf
* https://heartbeat.fritz.ai/how-to-fit-large-neural-networks-on-the-edge-eb621cdbb33
* https://cloud.google.com/solutions/machine-learning/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
* https://research.google/pubs/pub43146/
