# Principles for Engineering ML Systems in the Computing Continuum 

> This is a specialization of the [Advanced Topics in Software Systems course](../README.md) with a focus on *Principles for ML services in the Computing Continuum*.

**Professor**: 
> [Hong-Linh Truong](https://users.aalto.fi/~truongh4/)

**Target students**: 
> Master and PhD students in CS.

## Introduction

Complex Machine Learning (ML) applications and services and their reliability and robustness are strongly dependent on the underlying systems empowering such applications and services. On the one hand, techniques for supporting performance engineering, configuration management, testing and debugging of ML are extremely important. On the other hand, large-scale distributed systems and new computing models  have evolved into the Computing Continuum in which  new hardware and infrastructure architectures, such as robotic swarms, AI accelerators,  and 5G networks, are blended with IoT, edge systems and cloud infrastructures to provide a continuum capabilities for various emerging application requirements. Such systems and computing models are being exploited for advanced ML applications and services. Developing and optimizing  ML applications and services in the Computing Continuum require in-depth understanding of the systems and the roles of systems for  ML.  This course will study key principles for engineering such ML systems in the Computing Continuum. 

## Objectives

The study is centered around researching new ideas, evaluating existing techniques, optimizing systems and exploring new solutions for engineering service-based ML systems in the Computing Continuum. Students will be able to:

* understand key characteristics of the Computing Continuum
* classify and explain state of the art of systems requirements for service-based ML systems 
* analyze and apply key metrics and system designs of service-based ML systems 
* define and develop reliability and performance monitoring and analysis of service-based ML systems
* apply and evaluate key programming models and frameworks for service-based ML systems
* produce and evaluate edge system designs for service-based ML systems


## Schedule


- **ML Systems and Computing Continuum**

- **Methods for ML Project Identification**: we will discuss about methods  for identifying an ML project to be carried out in the course

- **Robustness, Reliability, Resilience and Elasticity for ML Systems**:
  - Reading
    - [Coordination-aware assurance for end-to-end machine learning systems: the R3E approach](https://www.researchgate.net/publication/341762862_R3E_-An_Approach_to_Robustness_Reliability_Resilience_and_Elasticity_Engineering_for_End-to-End_Machine_Learning_Systems), 2022
    - [The New Frontier of Machine Learning Systems](https://arxiv.org/pdf/1904.03257.pdf)
    - [Hidden Technical Debt in Machine Learning Systems](https://proceedings.neurips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html)
    - [Declarative Machine Learning Systems](https://queue.acm.org/detail.cfm?id=3479315)
    - [Technology readiness levels for machine learning systems](https://www.nature.com/articles/s41467-022-33128-9)

- **End-to-end ML Systems Development**:
  - Reading:
    - [Developments in MLflow: A System to Accelerate the Machine Learning Lifecycle](https://dl.acm.org/doi/abs/10.1145/3399579.3399867)
    - [ModelDB: a system for machine learning model management](https://dl.acm.org/doi/10.1145/2939502.2939516)
  - [Hands-on for End-to-end ML systems development](../tutorials/MLProjectManagement/)

- **Monitoring and Observability for ML Systems**
  - Reading:
    - [Benchmarking big data systems: A survey](https://www.sciencedirect.com/science/article/pii/S0140366419312344)
    - [MLPERF Training Benchmark](https://arxiv.org/pdf/1910.01500.pdf)
    - [Data Validation for Machine Learning](https://mlsys.org/Conferences/2019/doc/2019/167.pdf)  
    - [Machine Learning Testing: Survey, Landscapes and Horizons](https://ieeexplore.ieee.org/document/9000651)
    - [MLCommons](https://mlcommons.org/en/)
    - [Putting Machine Learning into Production Systems](https://queue.acm.org/detail.cfm?id=3365847)

- **Tools and Practices for Observability and Monitoring**
    - [Hands-on for Observability and Monitoring](../tutorials/PerformanceMonitoring)

- **Coordination Models and Techniques for Machine Learning**:
  - Reading:
    - [Cirrus: a Serverless Framework for End-to-end ML Workflows](https://doi.org/10.1145/3357223.3362711)
    - [Towards ML Engineering: A Brief History Of TensorFlow Extended (TFX)](https://arxiv.org/abs/2010.02013)
    - [Orchestrating Big Data Analysis Workflows in the Cloud: Research Challenges, Survey, and Future Directions](https://dl.acm.org/doi/fullHtml/10.1145/3332301)
    - [KeystoneML: Optimizing Pipelines for Large-Scale Advanced Analytics](https://shivaram.org/publications/keystoneml-icde17.pdf)
    - [Jeff Smith. 2018. Machine Learning Systems: Designs that scale (1st. ed.). Manning Publications Co., USA.](https://www.manning.com/books/machine-learning-systems)
    - [Prediction-Serving Systems](https://queue.acm.org/detail.cfm?id=3210557)

- **ML Serving**
  - Reading:
  - [Hands-on for Machine Learning Serving](../tutorials/MLService-2022/README.md)

- **Qualty of Analytics for ML**:
  - Reading:
      - [QoA4ML -A Framework for Supporting Contracts in Machine Learning Services](https://research.aalto.fi/files/65786264/main.pdf), The 2021 IEEE International Conference on Web Services (ICWS 2021).
      - [Enabling Awareness of Quality of Training and Costs in Federated Machine Learning Marketplaces](https://research.aalto.fi/files/105781165/Enabling_Awareness_of_Quality_of_Training_and_Costs_in_Federated_Machine_Learning_Marketplaces.pdf), UCC 2022
  - [QoA4ML](https://github.com/rdsea/QoA4ML/)
  - [QoA hands-on](../tutorials/qoa4ml-2022)

- **Edge Machine Learning**
  - Reading:
    - [Serving deep neural networks at the cloud edge for vision applications on mobile platforms](https://dl.acm.org/doi/10.1145/3304109.3306221)
    - [From the Edge to the Cloud: Model Serving in ML.NET](http://sites.computer.org/debull/A18dec/p46.pdf)
    - [Machine Learning at Facebook:Understanding Inference at the Edge](https://research.fb.com/wp-content/uploads/2018/12/Machine-Learning-at-Facebook-Understanding-Inference-at-the-Edge.pdf)
    - [Distributing Deep Neural Networks with Containerized Partitions at the Edge](https://www.usenix.org/system/files/hotedge19-paper-zhou.pdf)
    - [A survey of federated learning for edge computing: Research problems and solutions](https://www.sciencedirect.com/science/article/pii/S266729522100009X)

## Project

Students will be grouped to work on a mini project.
