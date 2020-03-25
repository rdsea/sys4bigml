# 1. Prometheus
Prometheus is an open-source metrics-based monitoring systems which is widely used by many companies and organizations for monitoring their applications and infrastructures. Mainly, prometheus provides the following components:

- Prometheus server - This scrapes and stores time series data from client systems and applications.
- Exporters - used in exporting existing metrics from third-party systems as Prometheus metrics.
- An alertmanager used to handle alerts
- The client libraries for instrumenting application code

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
  a. Install docker
  
     The instruction is [doc_docker](https://docs.docker.com)
     
  b. Install docker-compose
  
     The instruction is [doc_docker-compose](https://docs.docker.com/compose/install)

### 2.4 Set up Prometheus, add Exporter and install Grafana
  a. Introduce prometheus.yml
  b. Introduce docker-compose file
  
      - Configure prometheus
      - Add exporter
      - Add visualization with Grafana
      
  The information of this installation is at this [link](https://dzone.com/articles/monitoring-with-prometheus)

## 3. Examples:

* 3.1 Monitoring a server

    Monitoring a server using [Node_Exporter](https://version.aalto.fi/gitlab/sys4bigml/sys4bigml-2020/tree/master/tutorials/PerformanceMonitoring/Node_Exporter)


* 3.2 Monitoring a Linux process
  
    Monitoring a process using [Pushgateway](https://version.aalto.fi/gitlab/sys4bigml/sys4bigml-2020/tree/master/tutorials/PerformanceMonitoring/Pushgateway)


* 3.3 Monitoring an application

    Monitoring an application using [Client library](https://version.aalto.fi/gitlab/sys4bigml/sys4bigml-2020/tree/master/tutorials/PerformanceMonitoring/ClientLibrary)

      
