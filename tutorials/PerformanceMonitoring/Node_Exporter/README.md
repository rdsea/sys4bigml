# Node Exporter
The node exporter is a built-in program that can be used to extract information of your machine. 
Note exporter can be executed as a binary file. Go to the path "http://yourhost:9100/metrics" to verify that the node exporter is correctly up and running. Notably, you should select the right version of node exporter for your machine, for instance, linux, window, etc.
For using a node exporter, you can follow the instruction below:

## Prometheus Configuration
Perform the modifications for the prometheus.yml file such as follows:
```properties
static_configs:
    - targets: ['localhost:9090', 'localhost:9100']
```
or if you run Prometheus through docker:
```properties
static_configs:
    - targets: ['localhost:9090', 'your_ip_address:9100']
```
You can also modify the scrape_interval to an arbitrary number upon your demand.
```console
user@test:~$ ./prometheus

```

## Grafana
After grafana is executed, you can go to its address at http://yourhost:3000 and follow the instructions until you see the login screen. The default user:password of grafana is admin:admin. You have to change your password at the first login.

### Add datasource
You have to add a data source from Grafana dashboard. Choose Prometheus

### Import dashboard
You can use the variety of existing dashboards of grafana from the website https://grafana.com/grafana/dashboards. Select Prometheus as the datasource for your dashboard and you will see the metrics monitoring by the exporters in your dashboard.

## References

* https://devconnected.com/the-definitive-guide-to-prometheus-in-2019
* https://devconnected.com/complete-node-exporter-mastery-with-prometheus
