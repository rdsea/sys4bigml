# Monitoring ML systems and application

## Overview
 The goal of this tutorial is to equip the students with basic skills to monitor their real ML systems and applications. Students will study the provided components to monitor ML services. This will involve the monitoring of different layers and corresponding components, such as the infrastructural layer (e.g., VM), the platform layer (e.g., a middleware), and the application layer (such as ML service).





  arbitrary application through three examples. Examples include:
* Monitoring a server: Monitor a server using [Node_Exporter](Node_Exporter/README.md)


* Monitoring a Linux process: Monitor a system process using [Pushgateway](Pushgateway/README.md).


* Monitoring an application: Monitor an arbitrary application using [Client library](ClientLibrary/README.md).

## Basic monitoring tools/frameworks

We will use [Prometheus](https://prometheus.io/) - a very popular open-source monitoring system which is widely used by many companies and organizations for monitoring their applications and infrastructures. Following Prometheus document to study and install main features of Prometheus, especially the following components:
- Prometheus server - used to scrape and store data from client systems and applications.
- Exporters - used in exporting existing metrics from third-party systems as Prometheus metrics.
- Pushgateway - used to handle push information from targets
- The client libraries - used for instrumenting application codes

Furthermore, we will use [Grafana]() for performance visualization.

Following the following links to setup Prometheus and Grafana:
* https://prometheus.io/docs/prometheus/latest/getting_started/
* Node Exporter [Download](https://github.com/prometheus/node_exporter/releases/download/v0.18.1/node_exporter-0.18.1.linux-amd64.tar.gz)
* Grafana (used in Node Exporter example) [Download](https://dl.grafana.com/oss/release/grafana-6.6.0.linux-amd64.tar.gz)
* Pushgateway (used in Pushgateway example) [Download](https://github.com/prometheus/pushgateway/releases/download/v1.1.0/pushgateway-1.1.0.linux-amd64.tar.gz
* https://dzone.com/articles/monitoring-with-prometheus

## Preparing an ML service

>TODO: to be written

Before practicing the monitoring for a machine learning service, we will deploy a simple REST-based machine learning service. We will
* use a [BTS Prediction model]()
* make a simple REST ML service, use [the template and a local version](MLService/)
* test if the ML service work
```
$python MySimpleMLService.py
```
and
```
$curl -X GET http://localhost:8001
$curl -X GET http://localhost:8000
```
if you see the ML service work and the metrics are outputed, then [configure Promethesus to pull metrics](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config) from your Prometheus endpoint in your ML service.

```
static_configs:
  - targets: ['your_ip_address:8000']
```
Then check the metrics of your ML service in Prometheus/Grafana:
>TODO 
Also see our [ML serving tutorial](../MLServing/)

## References

* https://github.com/prometheus/client_python
* https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config
* https://dzone.com/articles/monitoring-with-prometheus
* https://devconnected.com/complete-node-exporter-mastery-with-prometheus
* https://devconnected.com/monitoring-linux-processes-using-prometheus-and-grafana
* https://github.com/rycus86/prometheus_flask_exporter
* https://sysdig.com/blog/prometheus-metrics

## Open Questions

1. How to monitor a machine learning pipeline with Prometheus?

2. How to make an alert for the specific conditions of metrics detected in your machine learning programs or systems with Prometheus?

3. How to monitor multiple nodes or a cluster using Prometheus? What is about the monitoring of a Kubernetes cluster?
