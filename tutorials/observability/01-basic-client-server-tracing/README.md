# 01-basic-client-server-tracing

## Study goals
- Give an example/feeling of setting an end-to-end trace from client-server application
  - Architecture for an end-to-end trace
  - Introduce various instrumentations:
    - Zero-code instrumentation
    - Lib-based instrumentation
    - Manual instrumentation
  - Collector with Otel collector
    - setting and components
  - Distributed tracing backbend with Jaeger

## Prerequisites
Before you begin, ensure you have the following installed:
- Python 3.8+
- Docker and Docker Compose
- `virtualenv` (or use `python -m venv`)

## Tools and Technologies
This tutorial uses the following tools and technologies:
- **Python**: The programming language for the application.
  - **Flask**: A micro web framework for the server.
  - **Requests**: A library for making HTTP requests for the client.
- **OpenTelemetry**: An observability framework for generating and collecting telemetry data (traces, metrics, logs).
- **Jaeger**: A distributed tracing system for monitoring and troubleshooting microservices-based distributed systems.
- **Docker**: A platform for developing, shipping, and running applications in containers.

## Application Overview
The [example application from opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python/tree/main/docs/examples/auto-instrumentation) consists of a simple client and server:
- Create `application/` and copy client-server* application from opentelemetry-python example to
- `application/client.py`: A Python script that sends requests to the server.
- `application/server_automatic.py`, `application/server_manual.py`, `application/server_programmatic.py`: Three versions of a Flask-based server, each demonstrating a different way to instrument with OpenTelemetry.

## Hands-on Steps

### Part 1: Initial Setup
1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install opentelemetry-distro opentelemetry-exporter-otlp flask requests
   opentelemetry-bootstrap -a install
   ```
   **Note on `uv`:** If you are using `uv`, you might encounter issues with `opentelemetry-bootstrap -a install`. Please check this [troubleshooting guide](https://opentelemetry.io/docs/zero-code/python/troubleshooting/#bootstrap-using-uv).

### Part 2: Tracing to the Console
This part demonstrates how to generate traces and print them to the console using different instrumentation methods.

#### Method A: Zero-Code Instrumentation (Automatic)
This method requires no code changes to the application.

1. **Start the server:**
   ```bash
   opentelemetry-instrument \
       --traces_exporter console \
       --service_name server-auto \
       python application/server_automatic.py
   ```

2. **In a separate terminal, run the client:**
   ```bash
   python application/client.py "hello"
   ```
   You should see trace information printed to the console where the server is running.

#### Method B: Programmatic Instrumentation (With a library)
This method uses the `FlaskInstrumentor` library to automatically instrument the Flask application.

1. **Start the server:**
   ```bash
   python application/server_programmatic.py
   ```

2. **In a separate terminal, run the client:**
   ```bash
   python application/client.py "world"
   ```
   Again, you will see trace information in the server's console.

#### Method C: Manual Instrumentation (SDK)
This method demonstrates how to manually create spans and traces using the OpenTelemetry SDK.

1. **Start the server:**
   ```bash
   python application/server_manual.py
   ```

2. **In a separate terminal, run the client:**
   ```bash
   python application/client.py "manual"
   ```
   Traces will be printed to the server's console.

### Part 3: Tracing with Jaeger
Now, let's send the traces to a Jaeger backend instead of the console.

1. **Start Jaeger:**
   Run the following command to start a Jaeger container. You can access the Jaeger UI at `http://localhost:16686`.
   ```bash
   docker run --rm --name jaeger \
     -p 16686:16686 \
     -p 4317:4317 \
     -p 4318:4318 \
     cr.jaegertracing.io/jaegertracing/jaeger:2.9.0
   #cr.jaegertracing.io/jaegertracing/all-in-one:latest
   ```

2. **Run the application with the OTLP exporter:**
   Now, run the application again, but this time configure it to send traces to Jaeger via the OTLP (OpenTelemetry Protocol) exporter.

   **For Zero-Code Instrumentation:**
   ```bash
   opentelemetry-instrument \
       --traces_exporter otlp_proto_http \
       --exporter_otlp_endpoint "http://localhost:4318" \
       --service_name server-auto \
       python application/server_automatic.py
   ```

   **For Manual/Programmatic Instrumentation:**
   You will need to modify the server code to use the `OTLPSpanExporter`. In `server_manual.py` or `server_programmatic.py`, add the following:
   ```python
   from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
   from opentelemetry.sdk.trace.export import BatchSpanProcessor

   # ... (inside the setup code)
   provider = TracerProvider()
   set_tracer_provider(provider)

   # Export to Jaeger
   otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
   provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
   ```
   - A TracerProvider is responsible for creating tracers, and for managing how spans are processed and exported 
   - Created `provider` the global tracer provider; hence, whenever someone calls `trace.get_tracer(...)` use this provider
   Then run the client. You should be able to see the traces in the Jaeger UI.

### Part 4: Using the OpenTelemetry Collector
It's common to use an OpenTelemetry Collector to receive, process, and export telemetry data.

1. **Configure the Collector:**
   The configuration for the collector is in `config/otel-collector-config.yaml`. This collector is configured to receive OTLP data and export it to Jaeger.

2. **Start the Collector:**
   ```bash
   docker run --rm --name otelcol \
     -v "$(pwd)/config/otel-collector-config.yaml":/etc/otelcol-contrib/config.yaml \
     -p 4317:4317 -p 4318:4318 \
     otel/opentelemetry-collector-contrib:latest \
     --config /etc/otelcol-contrib/config.yaml
   ```

3. **Run Jaeger (if not already running):**
   - Ensure your Jaeger instance is running.
   - Ensure the docker network is the same between otel-collector and jaeger. O.w can use a docker compose file `deployment/app-otel-jaeger.yaml`

4. **Run the application:**
   Now, your application can send traces to the OpenTelemetry Collector (running on port 4317/4318), which will then forward them to Jaeger. The application configuration is the same as in Part 3.

   Run the client a few times, and you should see the traces appearing in the Jaeger UI. 
