# Advanced Topics in Software Systems

>This is an advanced research-based course for master and PhD students. The current focus of this course is on **Principles and techniques for Engineering Service-based Hybrid Intelligence Software Systems**.

## Overview
  
We have seen new waves of software systems that combines diverse types of capabilities delivered by edge and cloud services, Artificial Intelligence (AI) and Machine Learning (ML) services, Large Language Models (LLMs) and AI Agents, and emerging quantum computing as a service. The combination of these diverse types of capabilities creates a new, future wave of [so-called multi-continuum computing systems (MCS)](https://research.aalto.fi/files/198061514/multicontinuum.pdf) for solving complex problems: a MCS consists of and integrates capabilities from edge analytics, AI/ML services, cloud big data services, GenAI/LLMs,  and collectives of humans to provide advanced, on-demand, hybrid service-based software. Furthermore, an important aspect is the sovereignty of the software systems built with complex AI. How to avoid the disruption of critical AI functionality due to third party dependencies  become an important problem (the digital/technological sovereignty) that we need to examine carefully.

Our course will focus on:

- *Service-based hybrid intelligence software*.: Multi-continuum service-based software systems built with AI/ML/LLMs  capabilities and other types of software capabilities: 
 
- *Designs for requirements of intelligence continuum*:  combine AI/ML/LLMs with human intelligences for the software and  deploy the software atop edge-cloud computing infrastructures.

- *Trustworthiness, sovereignty and performance assurance*

## Target participants/learners

The course is for students in Doctoral and Master studies. In Aalto the course is for students in [Doctoral Programme in Science](https://into.aalto.fi/display/endoctoralsci/Courses+offered) and the [CCIS Master Programme](https://www.aalto.fi/en/programmes/masters-programme-in-computer-communication-and-information-sciences).

This course provides advanced knowledge about computing and software that are useful for distributed software systems, data platforms, smart services, and AI/ML systems. Therefore, it connects to various other courses, such as *[Big Data Platforms](https://github.com/rdsea/bigdataplatforms)*, *Cloud Computing*, *Deep Learning* and *Master thesis*, by providing complementary in-depth knowledge w.r.t software system aspects.

## Required previous knowledge

Students should have knowledge about cloud computing, big data, operating systems, distributed systems and AI/ML. Therefore, it is important that students have passed courses with these topics, such as *Cloud Computing*, *Big Data Platforms*, *Operating Systems*, and *Machine Learning*. Students are expected to be very good with programming skills as well.

## Content

*First*, characteristics as well as key system requirements due to the complexity, robustness and sovereignty of service-based hybrid intelligence software systems  will be analyzed and presented. Based on that we will learn techniques for supporting performance engineering, elasticity, and observability. Such techniques are extremely important; they are **cross-topics** for the course.

*Second*, selected topics in engineering service-based hybrid intelligence software systems will be presented. We will examine techniques for observability, vulnerability diagnostics, quality-aware and trustworthiness assurance. We will examine the state-of-the-art, strengths and weakness of concepts and techniques. We will focus on engineering frameworks that can be used to development and analytics of service-based hybrid intelligence software systems.  

*Third*, concrete course projects will be carried out to demonstrate the understanding and applicability of techniques for service-based hybrid intelligence software systems. With this, students will perform concrete design and implementation to test and apply learned concepts/techniques into real systems.

### Focused Areas in 2026

* Concepts of service-based hybrid intelligence software systems
* Techniques and models for design, evaluation and coordination of systems robustness, trustworthiness and performance for service-based hybrid intelligence software systems (with also engineering work)
* Observability and senario-based analytics experimentation for end-to-end service-based hybrid intelligence software systems (with also engineering work)
* Designs, trustworthiness, and analytics of hybrid intelligence software built with GenAI/LLMs in  edge-cloud continuum (with also engineering work)

## Course Plan and Teaching methods

We define the generic plan of the course as follows:

* Lectures given by teachers: students must provide study logs
* Hands-on tutorials given by teachers: the goal is to give some concrete examples of the techniques discussed in the lectures. However, since it is a research-oriented course, students can also practice similar problems with different software stack.
* Project topic proposal and presentation: students must identify a topic related to the content of the course and present it
* Topic implementation and demonstration: [students will implement the topic and demonstrate the project](demos.md)
* Students will make public material about the topic project available in Git spaces (e.g., in Aalto, Github, Gitlab, ...)

As an advanced and research-oriented course, we will use the pass/fail as a way to evaluate students. Passing the course will require the students to (i) participating in lectures and hands-on, (ii) passing study logs, (iii) passing project topic presentation, and (iv) passing the final demonstration.


## Fall 2026 - Schedule

* Responsible teacher: [Hong-Linh Truong](https://users.aalto.fi/~truongh4/)
*  Other teacher/assistant: [Hong-Tri Nguyen](https://hong3nguyen.github.io/) and [Korawit Rupanya](https://korawitrupanya.github.io/)
*  [Basic course management]()

### Tentative slots

Date|Place|Content|Lead person
---|---|---|---
02.09.2026 | |[Lecture 1 - Service-based Hybrid Intelligence Software Systems ](slides/) | Linh Truong
09.09.2026 ||[Lecture 2 -Observability and Analytics Experimentation](slides/) | Hong-Tri Nguyen
16.09.2026 | | [Lecture 3 Hands-on on Observability and Scenario-based Analytics Experimentation]() | Hong-Tri Nguyen, Korawit Rupanya
23.09.2026 | | [Lecture 4- Fundamental Design and Integration of LLM Workflows and Agentic AI](slides/)| Korawit Rupanya - Hong Tri Nguyen
30.10.2026 | | [Lecture 5 - Coordination, Trustworthiness, Sovereignty, and Performance Assurance](slides/)| Linh Truong
07.10.2026 |  |Topic Introduction/discussion| All
21.10.2026 | | Project progress presentation| All
28.10.2026 |flexible, R030A133 T5| Project topic discussion| All
04.11.2026 |  | Checkpoint 1: Topic progress discussion |  All
11.11.2026 |flexible | discussion about project progress| All
18.11.2026 | |Checkpoint 2: Topic progress presentation  | All
25.11.2026 | |Final project demonstration and demonstration| All
09.12.2026 | |Final report/code delivery  |  Individual

### Lectures/Discussions

- Lecture 1: **Service-based Hybrid Intelligence Software Systems**
- Lecture 2: **Observability and Analytics Experimentation**
- Lecture 3: **Hands-on on Observability and Scenario-based Analytics Experimentation**
- Lecture 4: **Fundamental Design and Integration of LLM Workflows and Agentic AI**
- Lecture 5: **Coordination, Trustworthiness, Sovereignty and Performance Assurance**

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
  - [Observability in term of Robustness for HIS-LLM in Multi continuum computing](./tutorials/r4hisllm)

### Project ideas presentations

  - Students will propose the project idea. This is an important aspect of *research-oriented course*. If a student cannot propose an idea, the teacher will suggest some concrete ideas for students.
  - Year 2026, two types of project ideas will be considered:
     - Systems/Tools for Optimizing Hybrid Software systems
     - HIS for Security/Compliance

### Final project demonstration

  - The final project demonstration is organized like an "event" where all students can demonstrate their work and students can discuss experiences in their projects.
  - [List of the student projects](demos.md)

### Guides

* [How to write study/learning logs](StudyLog.md)

## Reading list

* [Interesting and relevant papers and sites](ReadingList.md)

## Previous course versions

* [Fall 2025](./fall-2025/README.md)
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
