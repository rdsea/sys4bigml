# Node Exporter
The node exporter is a built-in program that can be used to extract information of your machine. For using a node exporter, you can follow the instruction below:

## Installation
First, user should download the exporter. Select the exporter for your system and execute it like a binary file. 
Notably, you do not have to set the exporter as a service in your system.

```console
user@test:~$ wget https://github.com/prometheus/node_exporter/releases/download/v0.18.1/node_exporter-0.18.1.linux-amd64.tar.gz

```

Go to the path "http://yourhost:9100/metrics" to verify that the node exporter is correctly up and running. Notably, you should select the right version of node exporter for your machine, for instance, linux, window, etc. After having the node exporter for your machine, you have to configure Prometheus and Grafana.


## Prometheus Configuration
Go to the download page and download the corresponding prometheus for your system. 

```console
user@test:~$ wget https://github.com/prometheus/prometheus/releases/download/v2.16.0-rc.0/prometheus-2.16.0-rc.0.linux-amd64.tar.gz

```
Extract the folder prometheus-version.targ.gz and go inside the folder. Then perform the modifications for the prometheus.yml file such as follows:
```properties
static_configs:
            - targets: ['localhost:9090', 'localhost:9100']
```  
You can also modify the scrape_interval to an arbitrary number upon your demand.

```console
user@test:~$ ./prometheus

```

## Grafana
head over to https://grafana.com/grafana/download and download the corresponding binary file for your system. Grafana will be used to visualize the data collected by prometheus.

```console
user@test:~$ wget https://dl.grafana.com/oss/release/grafana-6.6.0.linux-amd64.tar.gz 

```
After grafana is executed, you can go to its address at http://yourhost:3000 and follow the instructions until you see the login screen. The default user:password of grafana is admin:admin. You have to change your password at the first login.

### Add datasource
You have to add a data source from Grafana dashboard. Choose Prometheus

### Import dashboard
You can use the variety of existing dashboards of grafana from the website https://grafana.com/grafana/dashboards. Select Prometheus as the datasource for your dashboard and you will see the metrics monitoring by the exporters in your dashboard. 

## References

* https://devconnected.com/the-definitive-guide-to-prometheus-in-2019
* https://devconnected.com/complete-node-exporter-mastery-with-prometheus
      
