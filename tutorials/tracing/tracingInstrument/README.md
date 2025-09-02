# Teaching-tracinginstrument
The material from this hand-on is mostly from [OpenTelemetry Python documentation](https://opentelemetry.io/docs/zero-code/python/)

## Workflow

### Requirement
- We need to create virtualenv and then dependencies.

### UV
- Could some issues with "opentelemetry-bootstrap -a install", please check this [troubleshooting](https://opentelemetry.io/docs/zero-code/python/troubleshooting/#bootstrap-using-uv)

### rye

### virtualenv

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

## Application
- Flask-based client and server from [OpenTelemetry Python examples](https://github.com/open-telemetry/opentelemetry-python)

## Tracing with Flask-based client-server

### Zero-code
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
python <client_python>.py 

# E.g., from opentelemetry-python
python auto-instrumentation/client.py hong3nguyen 
```

### With code

#### Manual trace
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
#### Instrumentation libs

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


## Collector 

### Otel 

### Jaeger
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

--- 
## Download tutorials from opentelemetry-python with auto-instrumetation

```bash
git clone -n --depth=3 --filter=tree:0 https://github.com/open-telemetry/opentelemetry-python
cd opentelemetry-python
git sparse-checkout set --no-cone docs/examples/auto-instrumentation
git checkout
```


## Execute

### Server-manual

```bash
# 1st terminal
python server_manual.py

# 2nd terminal
python client.py YOLO # or any text you want 
```

### Server-automatic

```bash
# 1st terminal
opentelemetry-instrument --traces_exporter console --metrics_exporter none python server_automatic.py
# 2nd terminal
python client.py Hong3Nguyen # or any text you want 
```

### Server-programatic 

```bash
# 1st terminal
python server_programmatic.py
# 2nd terminal
python client.py Hong3Nguyen # or any text you want
```
