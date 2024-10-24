# Tracing Manual

The traditional setting for a distributed tracing in an example for our ML system as figure:
![A traditional setting with distributed tracing](img/traditional_tracing_sys.png)

This work is an example for a manual setting tracing data.
![An example for a trace tree (DAG) with spans](img/trace_spans.png)

## Requerement

- Install minikube
- Install kubectl
- Has DockerHub account

## Create container
```bash
# direct to the core place
cd /src/teaching_tracingmanual/

# Build docker for yourself if need o.w you can use from our site by skipping this step
./2-buildDocker.sh <DockerHub_username> deployment/app
# NOTE optional check QoA4ML 
#./3-changeQoA4MLversion
```
## Flow

1. Start Jaeger (backend collector for Visualization)
```bash
# start backend Jaeger
docker run --rm \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

2. OPTIONAL for monitoring probe and policies from the previous Hands-on
```bash
# Optional for policies and scalling from Minh-Tri Hands-on
kubectl apply -f opa.yaml 

# Optional for QoA4ML sending probe to message queue
kubectl apply -f rabbit.yaml
```

3. Deploy all applications from app folder 
```bash
kubectl apply -f deployment/app/.
```

4. Check localhost:16686 from Jaeger to capture traces from the system/pipeline
At this step, you may not see any results from Jaeger capturing trace data since the firewall drops the message from kubernetes.
As a solution for direct message from my minikube/pods to a docker service (Jaeger) is to allow a port 4318 since I am working on http. This protocol has default listening port with Jaeger setting.

```bash
# go to the firewall setting from my Ubuntu machine with sudo mode
vim /etc/nftables.conf

# allow port 4318 for example like below
flush ruleset

table inet filter {
        chain input {
                type filter hook input priority 0; policy accept;
                # Jaeger port
                tcp dport 4318 accept
        }
        chain forward {
                type filter hook forward priority 0;
        }
        chain output {
                type filter hook output priority 0;
        }
}

# then apply this new setting 
sudo nft -f /etc/nftables.conf 

```

With this setting of the firewall, you can allow the port from minikube to docker Jaeger.
