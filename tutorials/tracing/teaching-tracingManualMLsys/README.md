# Tracing Manual

## Requerement

- Install minikube
- Install kubectl
- Has DockerHub account

## Create container
```bash
# direct to the core place
cd /src/teaching_tracingmanual/

# Build docker for yourself if need o.w you can use from ourside
./2-buildDocker.sh <DockerHub_username> <Kubernetes_deployment_folder>

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
