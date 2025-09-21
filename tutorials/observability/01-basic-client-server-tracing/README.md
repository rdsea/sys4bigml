# 01-basic-client-server-tracing

# Study goals
- Give an example/feeling of setting an end-to-end trace from client-server application
  - Architecture for an end-to-end trace
  - Introduce various instrumentations:
    - Zero-code instrumentation
    - Lib-based instrumentation
    - Manual instrumentation
  - Collector with Otel collector
    - setting and components
  - Distributed tracing backbend with Jaeger

## Application
The material from this hand-on is mostly from Flask-based client and server [OpenTelemetry Python documentation](https://opentelemetry.io/docs/zero-code/python/)

## Workflow
- Client side sends requests to server 
- Trace data is generated from instrumentation step
  - to Console
  - to TracingBackend

### Virtual env setting
- We need to create virtualenv and then dependencies.

#### UV
- Could some issues with "opentelemetry-bootstrap -a install", please check this [troubleshooting](https://opentelemetry.io/docs/zero-code/python/troubleshooting/#bootstrap-using-uv)

#### virtualenv

- Create virtualenv 
```bash
mkdir auto-instrumetation
cd auto-instrumetation
python -m venv venv
source ./venv/bin/activate
```

- Install requirements
```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install

pip install flask requests
```


## Tracing with Flask-based client-server 

### To console

#### Zero-code
- Start a server with auto-instrumetation

```bash
opentelemetry-instrument \
    --traces_exporter console,otlp \
    --metrics_exporter console \
    --service_name your-service-name \
    --exporter_otlp_endpoint 0.0.0.0:4317 \
    python <server_python>.py

# E.g., from opentelemetry-python
# python auto-instrumentation/client.py yolo 
opentelemetry-instrument \
    --traces_exporter console,otlp \
    --metrics_exporter console \
    --service_name your-service-name \
    --exporter_otlp_endpoint 0.0.0.0:4317 \
    python server_automatic.py

```

- Start the client to interact with the server
```bash 
python <client_python>.py <any_text>

# E.g., from opentelemetry-python
python auto-instrumentation/client.py hong3nguyen 
```

#### With code

##### Manual trace
- Setup full manual/SDK instrumentation (spans, tracer/exporters)
- Start a server
  - 
```bash
python server_manual.py
```

- Start a client
```bash
python client.py 
```

##### Instrumentation libs

- Use an instrumentation library (e.g. FlaskInstrumentor) to add instrumentation with minimal changes
- Start a server
  - 
```bash
python server_programmatic.py
```

- Start a client
```bash
python client.py 
```

### Collector 

#### Otel 

```bash
docker pull otel/opentelemetry-collector-contrib:0.133.0
docker run otel/opentelemetry-collector-contrib:0.133.0
```

#### Jaeger
- 
```bash
docker run --rm --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 5778:5778 \
  -p 9411:9411 \
  cr.jaegertracing.io/jaegertracing/jaeger:2.9.0
```

#### Update Auto and manual

##### Auto
- Then need to change configuration for auto-instrumetation
- However, still [issues](https://github.com/open-telemetry/opentelemetry-collector/issues/6363)

```bash
python application/server_automatic.py \
opentelemetry-instrument \
  --traces_exporter otlp_proto_grpc \
  --exporter_otlp_endpoint localhost:4317 

```

##### Manual
- add those and comments TracerProvider 
```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# set_tracer_provider(TracerProvider())
# get_tracer_provider().add_span_processor(
#     BatchSpanProcessor(ConsoleSpanExporter())
# )

provider = TracerProvider()
set_tracer_provider(provider)

# Exporter to collector
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
```


### Collector
#### To OpenTelemetry Collector before Jaeger Collector
- add a collector configuration 

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    send_batch_size: 2 # export spans in batches of 10
    timeout: 1000ms # send batch every 1 second if not full
    send_batch_max_size: 10 # max spans per batch

exporters:
  # use the OTLP exporter instance that targets Jaeger OTLP gRPC
  otlp/jaeger:
    endpoint: "jaeger:4317" # if running in same Docker network use service name
    tls:
      insecure: true # fine for local testing

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/jaeger]
```

- start OpenTelemetry Collector
```bash

docker run --rm --name otelcol  \
  -v "./config/otel-collector-config.yaml":/etc/otelcol-contrib/config.yaml \
  -p 4317:4317 -p 4318:4318 \
  otel/opentelemetry-collector-contrib:0.133.0 \
  --config /etc/otelcol-contrib/config.yaml

```
### backbend

- Jaeger
```bash
docker run --rm --name jaeger  \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  cr.jaegertracing.io/jaegertracing/jaeger:2.9.0

```
