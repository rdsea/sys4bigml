# Pushgateway
The Pushgateway is another type of built-in program that you can send the collected metrics to it. After installing the pushgateway for your system, go to "http://yourhost:9091/metrics" (or the port that you have assigned) to check if it's up and running correctly. For using a pushgateway, you can follow the instructions below:

## Prometheus Configuration

Perform the modifications for the prometheus.yml file such as follows:
```properties
static_configs:
    - targets: ['localhost:9090', 'localhost:9091']
```
or if you run Prometheus through docker:
```properties
static_configs:
    - targets: ['localhost:9090', 'your_ip_address:9091']
```
You can also modify the scrape_interval to an arbitrary number upon your demand. Notably, the port number of pushgateway is different to the exporter's, so you have to change the port so prometheus can collect information from it correctly.

```console
user@test:~$ ./prometheus

```

## A small bash program

This bash program will loop forever and send the considered metric (forexample: cpu_usage) to the pushgateway, from there the metrics will be collected by prometheus.

```console
user@test:~$ ./run_bash_program.sh

```

You now go to prometheus http://yourhost:9090 and go to the 'Expression' field, type the words "cpu_usage". You should see the metrics in your browser.


## Reference

* https://devconnected.com/the-definitive-guide-to-prometheus-in-2019
* https://devconnected.com/monitoring-linux-processes-using-prometheus-and-grafana
