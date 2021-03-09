## 1. Overview
 The goal of this tutorial is to equip the students with basic skills to monitor their real systems and applications. Students will study the provided components to monitor different targets such as a machine or a server, a system process, and an arbitrary application through three examples. Examples include:
* Monitoring a server: Monitor a server using [Node_Exporter](Node_Exporter/README.md)


* Monitoring a Linux process: Monitor a system process using [Pushgateway](Pushgateway/README.md).


* Monitoring an application: Monitor an arbitrary application using [Client library](ClientLibrary/README.md).

## 2.Prometheus
Prometheus is an open-source metrics-based monitoring system which is widely used by many companies and organizations for monitoring their applications and infrastructures. Mainly, Prometheus provides the following components:

- Prometheus server - used to scrape and store data from client systems and applications.
- Exporters - used in exporting existing metrics from third-party systems as Prometheus metrics.
- Pushgateway - used to handle push information from targets
- The client libraries - used for instrumenting application codes

## 3. Prequesites
* `docker`
* `docker-compose`
* `prometheus`
* Node Exporter [Download](https://github.com/prometheus/node_exporter/releases/download/v0.18.1/node_exporter-0.18.1.linux-amd64.tar.gz)
* Grafana (used in Node Exporter example) [Download](https://dl.grafana.com/oss/release/grafana-6.6.0.linux-amd64.tar.gz)
* Pushgateway (used in Pushgateway example) [Download](https://github.com/prometheus/pushgateway/releases/download/v1.1.0/pushgateway-1.1.0.linux-amd64.tar.gz
)
## 4.Installation

### 4.1. Create Prometheus system group

```bash
    $ sudo groupadd --system prometheus
    $ grep prometheus /etc/group
    prometheus:x:999:
```

### 4.2. Create Prometheus system user

```bash
    $ sudo useradd -s /sbin/nologin -r -g prometheus prometheus
    $ id prometheus
    uid=999(prometheus) gid=998(prometheus) groups=998(prometheus)
```
## 4.3 Set up Prometheus, add Exporter and install Grafana

* Create prometheus.yml
* Create `docker-compose.yaml` file

      - Configure prometheus
      - Add exporter
      - Add visualization with Grafana

  The information of this installation is at this blog [link](https://dzone.com/articles/monitoring-with-prometheus) 



## References

* https://dzone.com/articles/monitoring-with-prometheus
* https://devconnected.com/complete-node-exporter-mastery-with-prometheus
* https://devconnected.com/monitoring-linux-processes-using-prometheus-and-grafana
* https://github.com/rycus86/prometheus_flask_exporter
* https://sysdig.com/blog/prometheus-metrics

## Open Questions

1. How to monitor a machine learning pipeline with Prometheus?

2. How to make an alert for the specific conditions of metrics detected in your machine learning programs or systems with Prometheus?

3. How to monitor multiple nodes or a cluster using Prometheus? What is about the monitoring of a Kubernetes cluster?
