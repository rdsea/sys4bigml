#!/bin/bash

docker run -p 8181:8181 openpolicyagent/opa:latest run --server --set=decision_logs.console=true &

sleep 10

docker run -p 9090:9090 -v `pwd`/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus &

docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management &