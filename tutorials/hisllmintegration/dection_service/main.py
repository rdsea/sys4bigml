# FastAPI imports
from fastapi import FastAPI, HTTPException
import os

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Prometheus metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
# Mount /metrics endpoint
from prometheus_client import make_asgi_app

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "detection_service")

# Configure OTEL Tracing (gRPC)
resource = Resource(attributes={"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Configure OTEL Metrics (Prometheus)
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

detection_counter = meter.create_counter(
    name="detection_requests_total",
    description="Total number of detection/world data requests",
    unit="1",
)

# ---------------------------------------------------------------------------
# The SAR world: six sectors of a disaster area, three drones, ground-truth
# detections from the on-board detectors. This service plays the role of the
# edge data plane (drone detectors + weather), exposed as REST tools that the
# agent_service can call.
# ---------------------------------------------------------------------------

SECTORS = ("A1", "A2", "A3", "B1", "B2", "B3")

DETECTIONS = {
    "A1": [{"kind": "debris", "confidence": 0.95, "pos": [12, 4]}],
    "A2": [{"kind": "person", "confidence": 0.91, "pos": [3, 18]},
           {"kind": "person", "confidence": 0.84, "pos": [5, 17]}],
    "A3": [],
    "B1": [{"kind": "person", "confidence": 0.62, "pos": [22, 9]}],
    "B2": [{"kind": "vehicle", "confidence": 0.77, "pos": [30, 2]}],
    "B3": [{"kind": "person", "confidence": 0.88, "pos": [14, 25]}],
}

DRONES = {
    1: {"battery": 84, "sector": "A2", "status": "airborne"},
    2: {"battery": 31, "sector": "B1", "status": "airborne"},
    3: {"battery": 67, "sector": "B3", "status": "charging"},
}

WEATHER = {"A1": "clear", "A2": "clear", "A3": "clear",
           "B1": "smoke", "B2": "clear", "B3": "wind"}

# FastAPI app
app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())
FastAPIInstrumentor.instrument_app(app)


@app.get("/sectors")
def list_sectors():
    detection_counter.add(1)
    with tracer.start_as_current_span("list_sectors"):
        return {"sectors": list(SECTORS)}


@app.get("/detections/{sector}")
def get_detections(sector: str):
    detection_counter.add(1)
    with tracer.start_as_current_span("get_detections") as span:
        span.set_attribute("sector", sector)
        if sector not in SECTORS:
            raise HTTPException(404, f"unknown sector {sector!r}")
        return {"sector": sector, "detections": DETECTIONS[sector]}


@app.get("/drones/{drone_id}")
def get_drone(drone_id: int):
    detection_counter.add(1)
    with tracer.start_as_current_span("drone_status") as span:
        span.set_attribute("drone.id", drone_id)
        if drone_id not in DRONES:
            raise HTTPException(404, f"unknown drone {drone_id!r}")
        return {"drone_id": drone_id, **DRONES[drone_id]}


@app.get("/weather/{sector}")
def get_weather(sector: str):
    detection_counter.add(1)
    with tracer.start_as_current_span("get_weather") as span:
        span.set_attribute("sector", sector)
        if sector not in SECTORS:
            raise HTTPException(404, f"unknown sector {sector!r}")
        return {"sector": sector, "conditions": WEATHER[sector]}
