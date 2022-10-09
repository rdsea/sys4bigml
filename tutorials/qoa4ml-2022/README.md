# Monitoring ML systems and application

## Overview

The goal of this tutorial is to equip the students with basic skills to monitor their real ML systems and applications. Students will study the provided components to monitor ML services. 


## Basic monitoring tools/frameworks

We will use [Prometheus](https://prometheus.io/) - a very popular open-source monitoring system that is widely used by many companies and organizations for monitoring their applications and infrastructures. Following Prometheus document to study and install the main features of Prometheus. Furthermore, we will use [Grafana](https://grafana.com/grafana/download) for performance visualization.

Following the following links to setup Prometheus and Grafana:
* [Prometheus](https://prometheus.io/docs/prometheus/latest/getting_started/)

* [Configurate Grafana with Prometheus](https://prometheus.io/docs/visualization/grafana/)
* [QoA4ML](https://pypi.org/project/qoa4ml/) 
* [Open Policy Agent](https://www.openpolicyagent.org/) 

## Identifying the goal of monitoring/observability

What is the goal of monitoring? Given an ML service, what would you like to monitor? Can you define high-level metrics that can be determined from low-level monitoring information? Have you considered all the stakeholders' needs for monitoring? Would these metrics satisfy future needs?

The goal of monitoring/observability must be done together with ML service design, not an afterthought.

## Preparing an ML service

In this tutorial, we would use the Object Detection as ML service that we developed for the [ML Serving tutorial](https://version.aalto.fi/gitlab/sys4bigml/cs-e4660/-/tree/master/tutorials/MLService-2022).

Before practicing the monitoring for a machine learning service, we will deploy some monitoring/observing services using the script: `OPA_agent/run.sh`

## Working on low-level monitoring features

In this step, you should work on the list of low-level metrics/data, probes:
* which metrics/ data you are interested in collecting?
* how do the metrics look like and what do you need to collect for the metrics?
* how does the monitoring/observability affect your ML service design?

## Instrumenting ML service
In this tutorial, we would monitor the MLService that has been developed in the [ML Serving tutorial](https://version.aalto.fi/gitlab/sys4bigml/cs-e4660/-/tree/master/tutorials/MLService-2022). Please follow its instructions to deploy the ML services.

Check the `conf/metric.json`, where we can practice adding more metrics.

### Configure Prometheus to monitor the ML Service
If you see the ML service work and the metrics are outputed, then [configure Prometheus to pull metrics](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config) from your Prometheus endpoint in your ML service.

* Check `prometheus.yml` in prometheus folder

While the ML service and client from previous tutorial are running, QoA4ML probes integrated inside ML services (sample code below) will push monitored metrics to a message broker. To collect these metrics, you can run the `collector.py` in `OPA_agent`. The application will public the metrics so that Prometheus and Grafana service can visualize them. 

```python
#################################################
# ------------ QoA Init ------------ #
client = "./conf/client.json"
connector = "./conf/connector.json"
metric = "./conf/metrics.json"
client_conf = qoa_utils.load_config(client)
client_conf["node_name"] = get_node_name()
client_conf["instance_id"] = get_instance_id()
connector_conf = qoa_utils.load_config(connector)
metric_conf = qoa_utils.load_config(metric)

qoa_client = Qoa_Client(client_conf, connector_conf)
qoa_client.add_metric(metric_conf["App-metric"], "App-metric")
metrics = qoa_client.get_metric(category="App-metric")
qoa_utils.proc_monitor_flag = True
qoa_utils.process_monitor(client=qoa_client,interval=client_conf["interval"], metrics=metric_conf["Process-metric"],category="Process-metric")

# ------------ QoA Report ------------ #
metrics['Responsetime'].set(time.time())
qoa_client.report("App-metric")
#################################################
```

## Practice
* Add more monitoring metrics by modifying `metrics.json` and `QoA Report` in source code of each service.
* Modify the OPA policies and contracts to monitor ML services.
* Monitoring QoA from client

## References
The key features of Prometheus and Grafana explained in this tutorial are based on Prometheus and Grafana tutorials/documents:
* https://github.com/prometheus/client_python
* https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config
* https://www.openpolicyagent.org/docs/latest/#running-opa

## Open Questions

1. We show the monitoring of an ML service but how would you monitor the whole ML system in which a ML service may be just a component? For example, the ML service will be behind a load balancer or ML services accept only data sent via a queue or data stored in cloud file systems?

2. How to make an alert for the specific conditions of metrics detected in your machine learning systems with Prometheus?

3. How to monitor multiple instances of ML services running in  a cluster? For example, we can deploy ML service instances in a Kubernetes cluster. 

## Contributions

Author:   Minh-Tri Nguyen, (tri.m.nguyen@aalto.fi)
Editor:   Linh Truong
