
# Advanced Topics in Software Systems (SYS4BIGML)

* Responsible teacher: [Hong-Linh Truong](https://users.aalto.fi/~truongh4/)
* Other teachers/Assistants: [Phuong Pham] and [Tri Nguyen](https://www.researchgate.net/profile/Minh_Tri_Nguyen5)

## Overview

Complex Big Data and Machine Learning (ML) applications and services and their reliability and robustness are strongly dependent on the underlying systems empowering such applications and services. On the one hand, techniques for supporting performance engineering, configuration management, testing and debugging of Big Data and ML are extremely important. On the other hand, large-scale distributed systems and new computing models  have been evolved with new hardware and infrastructure architectures, such as edge systems, tensor processing units,  and quantum  computing systems. Such systems and computing models are being exploited for advanced Big Data and ML applications and services. Developing and optimizing Big Data and ML applications and services in such systems and models require in-depth understanding of the systems and the roles of systems for Big Data and ML. Currently, we lack courses to deal with the above-mentioned issues, especially in-depth analysis and forward-looking research directions in (software) systems for Big Data and ML.  This course will study advanced topics in systems for big data and ML/AI.


## Study programme/major/minor/modules

The course is for students in [Doctoral Programme in Science](https://into.aalto.fi/display/endoctoralsci/Courses+offered) and the [CCIS Master Programme](https://into.aalto.fi/display/enccis/Computer+Science+%28CS%29+2018-2020), especially for *Big Data and Large-scale computing* track and *Software Systems and Technologies* track.

This course provides advanced knowledge about computing and software systems that are useful for big data and machine learning domains. Therefore, it connects to various other courses, such as *Big Data Platforms*, *Mobile Cloud Computing*, *Deep Learning* and *Master thesis*, by providing complementary in-depth knowledge w.r.t system aspects.

## Required previous knowledge/courses

Students should have knowledge about cloud computing, big data, operating systems, distributed systems and machine learning. Therefore, it is important that students have passed courses with these topics, such as *Mobile Cloud Computing*, *Big Data Platforms*, *Operating Systems*, and *Machine Learning*.

This course is an advanced one, aiming at supporting research topics in master theses and PhD studies. Therefore, it is not  a prerequisite for any course.

##  Content
*First*, key system requirements due to the complexity, reliability,  and robustness of Big Data and ML applications and services  will be analyzed and presented. Based on that we will learn techniques for supporting performance engineering, configuration management, testing and debugging of Big Data and ML. Such techniques are extremely important; they are **cross-topics** for the course, regardless of the underlying systems empowering Big Data and ML applications and services.

*Second*, selected areas in systems for Big Data and ML will be presented. For each selected area, we will examine the state-of-the-art, strengths and weakness of concepts and techniques. We will focus on engineering frameworks that can be used to development Big Data and ML, according to  the above-mentioned **cross-topics**.  The selected areas in 2020-2022 study plan will be:
* Dataflows/programming frameworks and orchestration techniques
* Edge systems and edge-cloud continuum systems
* New hardware architectures and quantum systems

**Cross-topics** in these selected areas will be studied. For each selected area, we will focus on the following aspects:
* understanding and applying key techniques and concepts
* analyzing/evaluating/creating (new) methods/techniques


### Focused Areas in 2020-2022

Advanced Topics in Systems for Big Data and ML will focus on the following areas:
*  Design and evaluation for systems robustness, reliability, resilience and elasticity for Big Data/ML (with also engineering work)
*  Test, debug, monitoring, and configuration management (with also engineering work)
*  Dataflows and Orchestration Frameworks for Big Data/ML (with also engineering work)
*  Edge systems and edge-cloud continuum for Big Data/ML (with also engineering work)
*  New hardware architectures and quantum systems for Big Data/ML (more on the concepts and state-of-the-art)

## Course Plan
Here are the generic plan of the course:
* Lectures given by teachers: students must provide study logs
* Hands-on tutorials given by teachers
* Project topic proposal and presentation: students must identify a topic related to the content of the course and present it
* Topic implementation and demonstration: students will implement the topic and demonstrate the project
* Students will make public material about the topic project available in Git spaces (e.g., in Aalto, Github, gitlab, ...)

Passing the course will require the students to (i) participating in lectures and hands-on, (ii) passing study logs, (iii) passing project topic presentation, and (iv) passing the final demonstration.

For the detailed plan, pls. check course versions and mycourses.aalto.fi information.

## Fall 2020 - Schedule and Content
### Lectures
- Lecture 1:
  - Slides: [Robustness, Reliability, Resilience and Elasticity (R3E) for Big Data/Machine Learning Systems](slides/cs-e4660-lecture1-r3e-design-v0.2.pdf)
  - Key reading 1: [R3E -An Approach to Robustness, Reliability, Resilience and Elasticity Engineering for End-to-End Machine Learning Systems](https://www.researchgate.net/publication/341762862_R3E_-An_Approach_to_Robustness_Reliability_Resilience_and_Elasticity_Engineering_for_End-to-End_Machine_Learning_Systems)
  - Key reading 2: [The New Frontier of Machine Learning Systems](https://arxiv.org/pdf/1904.03257.pdf)
- Lecture 2
  - Slides: [Benchmarking, Monitoring, Validation and Experimenting for
Big Data and Machine Learning Systems](slides/cs-e4660-lecture2-analytics-v0.2.1.pdf)
  - Key reading 1: [Benchmarking big data systems: A survey](https://www.sciencedirect.com/science/article/pii/S0140366419312344)
  - Key reading 2: [MLPERF Training Benchmark](https://arxiv.org/pdf/1910.01500.pdf)
  - Key reading 3: [Data Validation for Machine Learning](https://mlsys.org/Conferences/2019/doc/2019/167.pdf)
  - Key reading 4: [Developments in MLflow: A System to Accelerate the Machine Learning Lifecycle](https://dl.acm.org/doi/abs/10.1145/3399579.3399867) and [ModelDB: a system for machine learning model management](https://dl.acm.org/doi/10.1145/2939502.2939516)
  - Key reading 5: [Putting Machine Learning into Production Systems](https://queue.acm.org/detail.cfm?id=3365847)
  - Site 1: [AI Matrix](https://aimatrix.ai/en-us/index.html)
- Lecture 3
- Lecture 4
### Hands-on tutorials
  - [Machine Learning experiment management](./tutorials/MLProjectManagement/)
  - [Observability and Monitoring](./PerformanceMonitoring)
### Project ideas presentations
  - Students will propose the project idea. If a student cannot propose, the teacher will suggest some concrete ideas.
### Final project demonstration
### Guides
* [How to write study/learning logs](./StudyLog.md)

## Reading list
* [Interesting and relevant papers and sites](./ReadingList.md)
## Previous course versions

* [Initial seminar in Spring 2020](./spring-2020)

## Contact

[Linh Truong](linh.truong@aalto.fi)
