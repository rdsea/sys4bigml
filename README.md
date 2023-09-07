# Advanced Topics in Software Systems (SYS4BIGML)

>The current focus of this course is on **principles for engineering ML systems in the Computing Continuum**.

## Overview

This is an advanced course for master and PhD students. The current focus of this course is on **principles for engineering ML systems in the Computing Continuum**. Big Data  and Machine Learning (ML) applications and services and their reliability and robustness are strongly dependent on the underlying systems empowering such applications and services. On the one hand, techniques for supporting performance engineering, configuration management, testing and debugging of Big Data and ML are extremely important. On the other hand, large-scale distributed systems and new computing models  have been evolved with new hardware and infrastructure architectures, such as edge systems, tensor processing units,  and quantum  computing systems. This leads to the computing continuum for advanced Big Data and ML applications and services. Developing and optimizing Big Data and ML applications and services in such systems and models require in-depth understanding of the systems and the roles of systems for Big Data and ML.

## Target participants/learners

The course is for students in Doctoral and Master studies. In Aalto the course is for students in [Doctoral Programme in Science](https://into.aalto.fi/display/endoctoralsci/Courses+offered) and the [CCIS Master Programme](https://into.aalto.fi/display/enccis/Computer+Science+%28CS%29+2018-2020).

This course provides advanced knowledge about computing and software systems that are useful for big data and machine learning domains. Therefore, it connects to various other courses, such as *[Big Data Platforms](https://version.aalto.fi/gitlab/bigdataplatforms/cs-e4640)*, *Cloud Computing*, *Deep Learning* and *Master thesis*, by providing complementary in-depth knowledge w.r.t system aspects.

## Required previous knowledge

Students should have knowledge about cloud computing, big data, operating systems, distributed systems and machine learning. Therefore, it is important that students have passed courses with these topics, such as *Cloud Computing*, *Big Data Platforms*, *Operating Systems*, and *Machine Learning*. Students are expected to be very good with programming skills as well. 
 
##  Content

*First*, key system requirements due to the complexity, reliability,  and robustness of Big Data and ML applications and services  will be analyzed and presented. Based on that we will learn techniques for supporting performance engineering, configuration management, testing and debugging of Big Data and ML. Such techniques are extremely important; they are **cross-topics** for the course, regardless of the underlying systems empowering Big Data and ML applications and services.

*Second*, selected areas in systems for Big Data and ML will be presented. We will examine the computing continuum model, dataflows/programming frameworks and orchestration techniques. We will examine the state-of-the-art, strengths and weakness of concepts and techniques. We will focus on engineering frameworks that can be used to development Big Data and ML, according to  the above-mentioned **cross-topics**.  

 For each selected area, we will focus on the following aspects:
* understanding and applying key principles, techniques, and concepts
* analyzing/evaluating/creating (new) methods/techniques

### Focused Areas in 2023

* Computing continuum (edge systems, edge-cloud systems)  
* Design and evaluation for systems robustness, reliability, resilience and elasticity for Big Data/ML (with also engineering work)
* Observability and explainability for ML applications (with also engineering work)
* Dataflows and orchestration frameworks for Big Data/ML (with also engineering work)
* Quality of analytics for ML in  edge-cloud continuum (with also engineering work)

## Course Plan and Teaching methods

We define the generic plan of the course as follows:

* Lectures given by teachers: students must provide study logs
* Hands-on tutorials given by teachers: the goal is to give some concrete examples of the techniques discussed in the lectures. However, since it is a research-oriented course, students can also practice similar problems with different software stack.
* Project topic proposal and presentation: students must identify a topic related to the content of the course and present it
* Topic implementation and demonstration: [students will implement the topic and demonstrate the project](demos.md)
* Students will make public material about the topic project available in Git spaces (e.g., in Aalto, Github, Gitlab, ...)

As an advanced and research-oriented course, we will use the pass/fail as a way to evaluate students. Passing the course will require the students to (i) participating in lectures and hands-on, (ii) passing study logs, (iii) passing project topic presentation, and (iv) passing the final demonstration.


## Fall 2023 - Schedule

* Responsible teacher: [Hong-Linh Truong](https://users.aalto.fi/~truongh4/)
* Other teachers/assistants: [Tri Nguyen](https://www.researchgate.net/profile/Minh_Tri_Nguyen5)
### Tentative slots

Date|Content|Lead person
---|---|---
06.09.2023| Course overview, lecture 1 discussion | Linh Truong
13.09.2023 |Lecture 2 discussion | Linh Truong
20.09.2023 | Hands-on tutorial 1| Tri Nguyen
27.09.2023 | Lecture 3 discussion   |  Linh Truong
04.10.2023 | Lecture 4 discussion | Linh Truong
11.10.2023 | Hands-on tutorial 2| Tri Nguyen
18.10.2023 | Project topic discussion| Linh Truong, Tri Nguyen
  flexible | discussion about topics and possible hands-on  | all
8.11.2023 | Topic progress presentation |  All
22.11.2023  |prefinal checkpoint of progress| All
7.12.2023  | final project demonstration| All
15.2023  | final report/code  |  Individual

### Lectures/Discussions

- Lecture 1: **Robustness, Reliability, Resilience and Elasticity for Big Data/ML Systems**
  - Slides: [Robustness, Reliability, Resilience and Elasticity (R3E) for Big Data/Machine Learning Systems](slides/cs-e4660-lecture1-r3e-design-v0.5.pdf)
  - Key reading 1: [R3E -An Approach to Robustness, Reliability, Resilience and Elasticity Engineering for End-to-End Machine Learning Systems](https://www.researchgate.net/publication/341762862_R3E_-An_Approach_to_Robustness_Reliability_Resilience_and_Elasticity_Engineering_for_End-to-End_Machine_Learning_Systems)
  - Key reading 2: [The New Frontier of Machine Learning Systems](https://arxiv.org/pdf/1904.03257.pdf)
  - Key reading 3: [Hidden Technical Debt in Machine Learning Systems](https://proceedings.neurips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html)
  - Key reading 4: [Declarative Machine Learning Systems](https://queue.acm.org/detail.cfm?id=3479315)
  - Key reading 5: [Technology readiness levels for machine learning systems](https://www.nature.com/articles/s41467-022-33128-9)

- Lecture 2: **Monitoring, Observability and Explainability for Big Data and ML Systems**
  - Slides: [Benchmarking, Monitoring, Observability and Experimenting for
Big Data and Machine Learning Systems](slides/cs-e4660-lecture2-analytics-v0.4.pdf)
  - Key reading 1: [Benchmarking big data systems: A survey](https://www.sciencedirect.com/science/article/pii/S0140366419312344)
  - Key reading 2: [MLPERF Training Benchmark](https://arxiv.org/pdf/1910.01500.pdf)
  - Key reading 3: [Data Validation for Machine Learning](https://mlsys.org/Conferences/2019/doc/2019/167.pdf)
  - Key reading 4: [Developments in MLflow: A System to Accelerate the Machine Learning Lifecycle](https://dl.acm.org/doi/abs/10.1145/3399579.3399867) and [ModelDB: a system for machine learning model management](https://dl.acm.org/doi/10.1145/2939502.2939516)
  - Key reading 5:[Machine Learning Testing: Survey, Landscapes and Horizons](https://ieeexplore.ieee.org/document/9000651)
  - Site 1: [MLCommons](https://mlcommons.org/en/)
  - The collection of [Putting Machine Learning into Production Systems](https://queue.acm.org/detail.cfm?id=3365847) is also useful

- Lecture 3: **Coordination Models and Techniques for Big Data and Machine Learning**
  - Slides: [Coordination Models and Techniques for  Big Data and Machine Learning Systems](slides/cs-e4660-lecture3-coordination-serving-v0.4.pdf)
  - Key reading 1: [Cirrus: a Serverless Framework for End-to-end ML Workflows](https://doi.org/10.1145/3357223.3362711)
  - Key reading 2: [Towards ML Engineering: A Brief History Of TensorFlow Extended (TFX)](https://arxiv.org/abs/2010.02013)
  - Key reading 3: [Orchestrating Big Data Analysis Workflows in the Cloud: Research Challenges, Survey, and Future Directions](https://dl.acm.org/doi/fullHtml/10.1145/3332301)
  - Key reading 4: [KeystoneML: Optimizing Pipelines for Large-Scale Advanced Analytics](https://shivaram.org/publications/keystoneml-icde17.pdf)
  - Key reading 5: [Jeff Smith. 2018. Machine Learning Systems: Designs that scale (1st. ed.). Manning Publications Co., USA.](https://www.manning.com/books/machine-learning-systems)
  - Key reading 6: [Prediction-Serving Systems](https://queue.acm.org/detail.cfm?id=3210557)

- Lecture 4 **Machine Learning in Edge-Cloud Continuum**
  - Slides: [Machine Learning with Edge-centric Systems](slides/cs-e4660-lecture4-edgeml-v0.4.pdf)
  - Key reading 1: [Serving deep neural networks at the cloud edge for vision applications on mobile platforms](https://dl.acm.org/doi/10.1145/3304109.3306221)
  - Key reading 2:[From the Edge to the Cloud: Model Serving in ML.NET](http://sites.computer.org/debull/A18dec/p46.pdf)
  - Key reading 3: [Machine Learning at Facebook:Understanding Inference at the Edge](https://research.fb.com/wp-content/uploads/2018/12/Machine-Learning-at-Facebook-Understanding-Inference-at-the-Edge.pdf)
  - Key reading 4: [Distributing Deep Neural Networks with Containerized Partitions at the Edge](https://www.usenix.org/system/files/hotedge19-paper-zhou.pdf)
  - Key reading 5: [A survey of federated learning for edge computing: Research problems and solutions](https://www.sciencedirect.com/science/article/pii/S266729522100009X)

*If you need the sources of slides for your teaching, pls. contact [Linh Truong](https://users.aalto.fi/~truongh4/)*

### Hands-on tutorials

We have a few hands-on tutorials for the course that students can carry out for the study. Note that only 1-2 hands-on tutorials will be arranged by the teacher and teaching assistants.

  - [End-to-end ML systems development](./tutorials/MLProjectManagement/)
  - [Observability and Monitoring](./tutorials/PerformanceMonitoring)
  - [Machine Learning Serving](./tutorials/MLserving/README.md)
  - [Qualty of Analytics for ML](./tutorials/qoa4ml/README.md)
  - [Edge ML Pipeline](./tutorials/edgemodelop)
  - [Common tasks with Edge ML](./tutorials/edgemlcommons)

### Project ideas presentations

  - Students will propose the project idea. This is an important aspect of *research-oriented course*. If a student cannot propose an idea, the teacher will suggest some concrete ideas for students.

### Final project demonstration
  - The final project demonstration is organized like an "event" where all students can demonstrate their work and students can discuss experiences in their projects.
  - [List of the student projects](demos.md)

### Guides

* [How to write study/learning logs](StudyLog.md)

## Reading list

* [Interesting and relevant papers and sites](ReadingList.md)

## Previous course versions

* [Fall 2022](fall-2022/README.md)
* [Fall 2021](fall-2021/README.md)
* [Fall 2020](fall-2020/README.md)
* [Initial seminar in Spring 2020](spring-2020/README.md)


## Citation (if you use the material):

Hong-Linh Truong, *Advanced Topics in Software Systems*, https://version.aalto.fi/gitlab/sys4bigml/cs-e4660, 2020 [BIB Entry](site.bib)

**Copyrights/Licences: the lecture slides and course structure/info use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Individual tutorials have their own licenses ([Apache Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0))**

## Contact

[Linh Truong](linh.truong@aalto.fi)
