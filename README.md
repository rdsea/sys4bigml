# Advanced Topics in Software Systems

>This is an advanced research-based course for master and PhD students. The current focus of this course is on **Principles and techniques for Engineering Multi-Continuum Service-based Software Systems**.

## Overview
  
We have seen new waves of software systems that combines diverse types of capabilities delivered by edge and cloud services, Artificial Intelligence (AI) and Machine Learning (ML) services, Large Language Models (LLMs) and AI Agents, and emerging quantum computing as a service. The combination of these diverse types of capabilities creates a new, future wave of so-called multi-continuum computing systems (MCS) for solving complex problems: a MCS consists of and integrates capabilities from edge analytics, AI/ML services, cloud big data services, GenAI/LLMs,  and collectives of humans to provide advanced, on-demand, hybrid service-based software.

Our course will focus on:

- Multi-continuum service-based software systems: services/applications built with AI/ML/LLMs  capabilities and other types of software capabilities.
 
- Designed for requirements of time continuum (long running) and intelligence continuum (combined AI/ML/LLMs with human intelligences) and  deployed atop edge-cloud computing infrastructures (computing continuum).

## Target participants/learners

The course is for students in Doctoral and Master studies. In Aalto the course is for students in [Doctoral Programme in Science](https://into.aalto.fi/display/endoctoralsci/Courses+offered) and the [CCIS Master Programme](https://into.aalto.fi/display/enccis/Computer+Science+%28CS%29+2018-2020).

This course provides advanced knowledge about computing and software systems that are useful for software systems, data platforms, services computing and machine learning systems. Therefore, it connects to various other courses, such as *[Big Data Platforms](https://github.com/rdsea/bigdataplatforms)*, *Cloud Computing*, *Deep Learning* and *Master thesis*, by providing complementary in-depth knowledge w.r.t software system aspects.

## Required previous knowledge

Students should have knowledge about cloud computing, big data, operating systems, distributed systems and machine learning. Therefore, it is important that students have passed courses with these topics, such as *Cloud Computing*, *Big Data Platforms*, *Operating Systems*, and *Machine Learning*. Students are expected to be very good with programming skills as well.

## Content

*First*, characteristics as well as key system requirements due to the complexity, reliability,  and robustness of multi-continuum service-based software systems  will be analyzed and presented. Based on that we will learn techniques for supporting performance engineering, elasticity, and observability. Such techniques are extremely important; they are **cross-topics** for the course.

*Second*, selected areas in engineering multi-continuum service-based software systems will be presented. We will examine techniques for observability, vulnerability diagnostics, quality-aware and trustworthiness assurance. We will examine the state-of-the-art, strengths and weakness of concepts and techniques. We will focus on engineering frameworks that can be used to development and analytics of multi-continuum service-based software systems.  

*Third*, concrete course projects will be carried out to demonstrate the understanding and applicability of techniques for service-based software systems. With this, students will perform concrete design and implementation to test and apply learned concepts/techniques into real systems.

### Focused Areas in 2025

* Concepts of multi-continuum service-based software systems with computing continuum, time continuum and intelligence continuum
* Techniques and models for design, evaluation and coordination of systems robustness, reliability, resilience and elasticity for multi-continuum service-based systems (with also engineering work)
* Observability, vulnerability diagnostics, and explainability for end-to-end service-based systems built with ML/GenAI/LLMs capabilities (with also engineering work)
* Designs, trustworthiness, and analytics of hybrid intelligence software built with GenAI/LLMs in  edge-cloud continuum (with also engineering work)

## Course Plan and Teaching methods

We define the generic plan of the course as follows:

* Lectures given by teachers: students must provide study logs
* Hands-on tutorials given by teachers: the goal is to give some concrete examples of the techniques discussed in the lectures. However, since it is a research-oriented course, students can also practice similar problems with different software stack.
* Project topic proposal and presentation: students must identify a topic related to the content of the course and present it
* Topic implementation and demonstration: [students will implement the topic and demonstrate the project](demos.md)
* Students will make public material about the topic project available in Git spaces (e.g., in Aalto, Github, Gitlab, ...)

As an advanced and research-oriented course, we will use the pass/fail as a way to evaluate students. Passing the course will require the students to (i) participating in lectures and hands-on, (ii) passing study logs, (iii) passing project topic presentation, and (iv) passing the final demonstration.


## Fall 2025 - Schedule

* Responsible teacher: [Hong-Linh Truong](https://users.aalto.fi/~truongh4/)
*  Other teacher/assistant: [Hong-Tri Nguyen](https://hong3nguyen.github.io/) and [Korawit Rupanya]()

### Tentative slots

Date|Place|Content|Lead person
---|---|---|---
03.09.2025 | |[lecture 1 - Multi Continuum Computing: Service-based Applications and Systems]() | Linh Truong
10.09.2025 ||Lecture 2 - Robustness, Reliability, Resilience and Elasticity for multi-continuum service-based software systems | Linh Truong
17.09.2025 | | Observability, Vulnerability Diagnostics, and Explainability| Hong-Tri Nguyen
24.09.2025 | |Hands-on   |  Hong-Tri Nguyen
01.10.2025 | | Designs and Analytics of Hybrid Intelligence Software built with GenAI/LLMs| Korawit Rupanya 
08.10.2025 | |Topic Introduction/discussion| All
22.10.2025 | | Project progress presentation| All
29.10.2025 |flexible| Project topic discussion| All
05.11.2025 | | Checkpoint 1: Topic progress discussion |  All
12.11.2025 |flexible | discussion about project progress| All
19.11.2025 | |Checkpoint 2: Topic progress presentation  | All
26.11.2025 | |Final project demonstration and demonstration| All
10.12.2025 | |Final report/code delivery  |  Individual

### Lectures/Discussions

- Lecture 1: **Multi-continuum Service-based Software Systems**
- Lecture 2: **Principles and Techniques for Robustness Reliability, Resilience and Elasticity**
- Lecture 3: **Observability, Vulnerability Diagnostics, and Explainability**
- Lecture 4: **Hands-on**
- Lecture 5: **Designs and Analytics of Hybrid Intelligence Software built with GenAI/LLMs**

*If you need the sources of slides for your teaching, pls. contact [Linh Truong](https://users.aalto.fi/~truongh4/)*

### Hands-on tutorials

We have a few hands-on tutorials for the course that students can carry out for the study. Note that only 1-2 hands-on tutorials will be arranged by the teacher and teaching assistants.

  - [Tracing](./tutorials/tracing)
  - [End-to-end ML systems development](./tutorials/MLProjectManagement/)
  - [Observability and Monitoring of ML Services](./tutorials/PerformanceMonitoring)
  - [Machine Learning Serving](./tutorials/MLServing/README.md)
  - [Quality of Analytics for ML](./tutorials/qoa4ml/README.md)
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

* [Fall 2024](./fall-2024/README.md)
* [Fall 2023](./fall-2023/README.md)
* [Fall 2022](fall-2022/)
* [Fall 2021](fall-2021/README.md)
* [Fall 2020](fall-2020/README.md)
* [Initial seminar in Spring 2020](spring-2020/README.md)


## Citation (if you use the material):

Hong-Linh Truong, *Advanced Topics in Software Systems*, https://github.com/rdsea/sys4bigml, 2020 [BIB Entry](site.bib)

**Copyrights/Licences: the lecture slides and course structure/info use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Individual tutorials have their own licenses ([Apache Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0))**

## Contact

[Linh Truong](linh.truong@aalto.fi)
