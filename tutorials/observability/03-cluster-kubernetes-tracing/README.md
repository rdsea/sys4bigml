# 03-cluster-kubernetes-tracing

## Study goals
- Give an example for setting an end-to-end trace in a cluster environment 
  - internal tracing data flow
  - external tracing data flow

- Potential setting for an edge-cloud continuum 

## Assumption for edge-cloud environment setting
- The world network on a single machine
- Edge emulator - services are presented by docker-based containers
- Cloud emulator - cluster is presented by k8s-based emulation

## Application
The material from this hand-on is mostly from [Object-classification respository](https://github.com/rdsea/object_classification_v2.git)

## Requirement

### The 
```yaml
App
  ↓  (http 4318)
Collector (OTel)
  ↓  (OTLP gRPC 4317 or OTLP HTTP 4318)
Jaeger Collector
  ↓  (HTTPS 9200 w/ TLS+auth)
Elasticsearch
  ↑  (HTTPS 9200 w/ TLS+auth)
Jaeger Query
  ↓  (HTTP 16686)
User/UI
```

## Workflow

### Requisites for a cluster
- Cluster setting
```bash
minikube start --cpu=4

cd infrastructure
# install traefik
helm repo add traefik https://traefik.github.io/charts
helm repo update

kubectl create namespace traefik
helm install traefik traefik/traefik \
  --namespace traefik

# export IP for external
./metallb.sh # OR minikube tunnel

```

### Jaeger along with Elasticsearch
#### elasticsearch setting
```bash
cd infrastructure
helm repo add elastic https://helm.elastic.co
kubectl create namespace observability

helm install elasticsearch elastic/elasticsearch -n observability -f value_elasticsearch.yaml

kubectl get secret elasticsearch-master-certs -n observability -o jsonpath="{.data['ca\.crt']}" | base64 --decode > ca.crt

kubectl get secret -n observability elasticsearch-master-credentials -o yaml

kubectl create secret generic jaeger-es-ca \
  --from-file=ca.crt=./ca.crt \
  -n observability

# create username and password
 kubectl create secret generic jaeger-es-creds -n observability \
  --from-literal=ES_USERNAME=elastic \
  --from-literal=ES_PASSWORD='lDpWEaFcMHsJvKe7'
```

#### Collectors and query
- apply tracing configuration
```bash
cd deployment

kubectl apply -f .
```


#### Application setting
- apply application 
```bash
cd application/cluster

kubectl apply -f .

cd application/edge

docker compose up -d 
```

#### Test 
- source venv first
- remember execute at image/
> python client_processing.py --url http://preprocessing:5010/preprocessing


## Further investigation
```yaml
                +------------------+
                |     User/UI      |
                +------------------+
                        ↑
                        | HTTP Query
                        |
                +------------------+
                |  Jaeger Query    |
                |   (UI/Backend)   |
                +------------------+
                        ↑
                        | HTTP/gRPC
                        |
                +------------------+
                |  Jaeger Collector |
                |  (Elasticsearch)  |
                +------------------+
                        ↑
        ----------------|-----------------
        |               |                 |
        |               |                 |
+---------------+  +---------------+   +----------------+
| OTel Sidecar  |  |  Envoy Proxy  |   |  Application   |
| (Daemon/Side) |  | (Istio sidecar)|   |  (instrumented |
|               |  |               |   |   with SDK)    |
+---------------+  +---------------+   +----------------+
        ↑                  ↑                  ↑
        |                  |                  |
   OTLP/HTTP/gRPC       OTLP/HTTP/gRPC      SDK spans
   (forwarding)         (forwarding)        (business logic)
        |                  |                  |
        |                  |                  |
    App network        Service network      DB/HTTP calls, etc.
    traces only        traces only


```
## 3. Jaeger with Istio and Envoy
### Flowchart
```yaml
App Pod
  ↓   (traffic)
Envoy Sidecar (Istio Proxy) 
  |   1. Envoy generates traces
  ↓   2. (Telemetry API) OTLP gRPC 4317
Jaeger Collector (in istio-system)
  ↓   SPAN_STORAGE_TYPE=badger
Badger Storage (in /badger data) -- Could change to ElasticSearch/cassandra/clickhouse
  ↑
Jaeger Query (UI :16686, Service "tracing")
  ↓  (HTTP 16686)
User/UI

```
1. Minikube or cluster
2. Istio and enable label
3. deploy [Jaeger](https://istio.io/latest/docs/tasks/observability/distributed-tracing/jaeger/) and OPA yml
4. Apply external provider for Jaeger and OPA
5. enable label for OPA and apply [tracing](https://istio.io/latest/docs/tasks/observability/telemetry/) (this file allow to config with various sampling rate and other tags)
6. application

```bash
istioctl install --set profile=default -y; kubectl label namespace default istio-injection=enabled

kubectl apply -f jaeger-istio.yml
```

1. Envoy generates traces (This tells Istio all Envoy proxies in the mesh to generate spans and send them to Jaeger.)
  - sampling 100%
```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-default
  namespace: istio-system
spec:
  tracing:
    - providers:
        - name: jaeger
          customTags: # exampe for custom tag for span
            environment:
              literal:
                value: production
            team:
              literal:
                value: payments
      randomSamplingPercentage: 100

```
2. Envoy knows how to forward OTLP to Jaeger collector
```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    enableTracing: true
    defaultConfig:
      tracing: {} # disable legacy MeshConfig tracing options
    extensionProviders:
      - name: jaeger
        opentelemetry:
          service: jaeger-collector.istio-system.svc.cluster.local
          port: 4317
```
| Concept                     | YAML Section                       | Port / Protocol                |
| --------------------------- | ---------------------------------- | ------------------------------ |
| App traffic → Envoy sidecar | Telemetry CRD (`mesh-default`)     | n/a (sidecar generates spans)  |
| Envoy → Jaeger Collector    | IstioOperator `extensionProviders` | 4317 OTLP gRPC, 4318 OTLP HTTP |
| Collector → Badger storage  | Jaeger Deployment env vars         | `/badger/data`                 |
| Query UI → User             | Service `tracing`                  | 80 → 16686                     |
| Zipkin API support          | Service `zipkin`                   | 9411 → 9411                    |

# Multi-conitumm tracing
- Setup ingress via traefik for the collector and query
```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jaeger-ingress
  namespace: observability
spec:
  ingressClassName: traefik
  rules:
    - host: jaeger.hong3nguyen.com
      http:
        paths:
          - path: /v1/traces
            pathType: Prefix
            backend:
              service:
                name: jaeger-collector
                port:
                  number: 4318  # HTTP port of collector
          - path: /
            pathType: Prefix
            backend:
              service:
                name: jaeger-query
                port:
                  number: 16686
EOF
```




