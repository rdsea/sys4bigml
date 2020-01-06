# Introduction to Prometheus

## 1. Major components

* Prometheus server - This scrapes and stores time series data from client systems and applications.

* Exporters - used in exporting existing metrics from third-party systems as Prometheus metrics.

* An alertmanager used to handle alerts

* The client libraries for instrumenting application code

## 2. Installation

### 2.1. Create Prometheus system group
    $ sudo groupadd --system prometheus

    $ grep prometheus /etc/group
    prometheus:x:999:
 
### 2.2. Create Prometheus system user
    $ sudo useradd -s /sbin/nologin -r -g prometheus prometheus

    $ id prometheus
    uid=999(prometheus) gid=998(prometheus) groups=998(prometheus)
 
### 2.3. Install docker and docker-compose
  a. Install docker

  b. Install docker-compose

### 2.4 Set up Prometheus, add Exporter and install Grafana
  a. Introduce prometheus.yml

  b. Introduce docker-compose file
  
      * Configure prometheus
      * Add exporter
      * Add visualization with Grafana

## 3. Some examples:

### 3.1 Monitoring a server
    o Example 1

### 3.2 Monitoring a Linux process
    o Example 2

### 3.3. Monitoring disk I/O using Exporter
    o Example 3

### 3.4 Monitoring an application
    o Example 4


      
