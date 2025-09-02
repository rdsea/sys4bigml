# Tracing in a cluster 

## Prerequisite

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
# Cluster tracing
## 1. Jaeger along with Elasticsearch
### Flowchart
```yaml
App
  ↓  (Jaeger thrift UDP 6831)
Sidecar (OTel)
  ↓  (OTLP gRPC 4317 or OTLP HTTP 4318)
Jaeger Collector
  ↓  (HTTPS 9200 w/ TLS+auth)
Elasticsearch
  ↑  (HTTPS 9200 w/ TLS+auth)
Jaeger Query
  ↓  (HTTP 16686)
User/UI
```

## 2. Otel and Jaeger collectors along with Elasticsearch
### Flowchart
```yaml
App
  ↓  (Jaeger thrift UDP 6831)
Sidecar (OTel)
  ↓  (OTLP gRPC 4317 or OTLP HTTP 4318)
Otel-to-Jaeger Collector
  ↓  (OTLP gRPC 4317)
Jaeger Collector
  ↓  (HTTPS 9200 w/ TLS+auth)
Elasticsearch
  ↑  (HTTPS 9200 w/ TLS+auth)
Jaeger Query
  ↓  (HTTP 16686)
User/UI
```

## 3. Jaeger with Istio and Envoy
### Flowchart
```yaml
App Pod
  ↓   (traffic)
Envoy Sidecar (Istio Proxy) 
  |   1. Envoy generates traces  <--------- Importance is here via "mesh-default"
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




