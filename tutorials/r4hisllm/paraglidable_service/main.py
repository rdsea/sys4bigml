# FASTAPI imports
from fastapi import FastAPI
import requests, datetime, os
from dotenv import load_dotenv

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Prometheus metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider, Counter
# Mount /metrics endpoint
from starlette.middleware.wsgi import WSGIMiddleware
from prometheus_client import make_asgi_app

# Load environment variables
load_dotenv()
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT_GRPC")
SERVICE_NAME = os.getenv("PARAGLIDABLE_OTEL_SERVICE_NAME")
PARAGLIDABLE_KEY = os.getenv("PARAGLIDABLE_KEY")

# Configure OTEL Tracing (gRPC)
resource = Resource(attributes={"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
)
tracer_provider.add_span_processor(processor)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Configure OTEL Metrics (Prometheus)
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Counter for number of /spots calls
spots_counter = meter.create_counter(
    name="paraglidable_spots_requests_total",
    description="Total number of /spots requests",
)

# FastAPI app
app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

# Simple cache
CACHE = {"timestamp": None, "data": None}
CACHE_TTL_SECONDS = 3600

@app.get("/spots")
def get_spots():
    # Increment Prometheus counter
    spots_counter.add(1)

    with tracer.start_as_current_span("get_spots"):
        now = datetime.datetime.utcnow()

        if CACHE["data"] and CACHE["timestamp"]:
            if (now - CACHE["timestamp"]).seconds < CACHE_TTL_SECONDS:
                return {"spots": CACHE["data"]}

        url = f"https://api.paraglidable.com/?key={PARAGLIDABLE_KEY}&format=JSON"
        api_data = requests.get(url).json()
        all_spots = []

        for date, spots in api_data.items():
            for s in spots:
                all_spots.append({
                    "name": s.get("name"),
                    "lat": s.get("lat"),
                    "lon": s.get("lon"),
                    "forecast": s.get("forecast"),
                    "date": date
                })

        CACHE["data"] = all_spots
        CACHE["timestamp"] = now
        return {"spots": all_spots}
