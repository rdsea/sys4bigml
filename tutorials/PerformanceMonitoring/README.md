# 1. Prometheus
Prometheus is an open-source metrics-based monitoring systems which is widely used by many companies and organizations for monitoring their applications and infrastructures. Mainly, prometheus provides the following components:

- Prometheus server - used to scrape and store data from client systems and applications.
- Exporters - used in exporting existing metrics from third-party systems as Prometheus metrics.
- Pushgateway - used to handle push information from targets
- The client libraries - used for instrumenting application code

In this tutorial, students will study the provided components to monitor different targets such as a machine or a server, a system process, and an arbitrary application. The goal of this tutorial is to equip the students with basic skills to monitor their real systems and applications. 

## 2. Installation

### 2.1. Create Prometheus system group

```bash
    $ sudo groupadd --system prometheus
    $ grep prometheus /etc/group
    prometheus:x:999:
``` 

### 2.2. Create Prometheus system user

```bash
    $ sudo useradd -s /sbin/nologin -r -g prometheus prometheus
    $ id prometheus
    uid=999(prometheus) gid=998(prometheus) groups=998(prometheus)
```

### 2.3. Install docker and docker-compose
* Install docker
  
     The instruction is [doc_docker](https://docs.docker.com)
     
* Install docker-compose
  
     The instruction is [doc_docker-compose](https://docs.docker.com/compose/install)

### 2.4 Set up Prometheus, add Exporter and install Grafana

* Introduce prometheus.yml
* Introduce docker-compose file
  
      - Configure prometheus
      - Add exporter
      - Add visualization with Grafana
      
  The information of this installation is at this blog [link](https://dzone.com/articles/monitoring-with-prometheus)

## 3. Examples:

* 3.1 Monitoring a server

In this example, student will learn how to monitor a server using [Node_Exporter](https://version.aalto.fi/gitlab/sys4bigml/sys4bigml-2020/tree/master/tutorials/PerformanceMonitoring/Node_Exporter). Node Exporter is provided by Prometheus, students only need to select the correct version of it corresponding to the operating system.


* 3.2 Monitoring a Linux process
  
This example introduces how to monitor a system process using [Pushgateway](https://version.aalto.fi/gitlab/sys4bigml/sys4bigml-2020/tree/master/tutorials/PerformanceMonitoring/Pushgateway). Pushgateway is available for download according to different operating systems.


* 3.3 Monitoring an application

Finally, students will study monitoring an arbitrary application using [Client library](https://version.aalto.fi/gitlab/sys4bigml/sys4bigml-2020/tree/master/tutorials/PerformanceMonitoring/ClientLibrary). Client library provided by Prometheus is more flexible so students can use its API to monitor the operations of an application.

      
