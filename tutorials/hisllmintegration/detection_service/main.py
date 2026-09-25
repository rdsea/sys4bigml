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
# Which data source to serve: "mock" (built-in example data) or "real".
DETECTION_SOURCE = os.getenv("DETECTION_SOURCE", "mock")

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
# Data sources
#
# This service is the edge data plane: drone detections, drone status and
# weather, exposed as REST tools the agent can call. The endpoints below only
# talk to a `source`, so you can swap the built-in mock data for a real
# detection system by implementing `RealSource` and setting
# DETECTION_SOURCE=real. Nothing in the agent needs to change.
#
# Contract every source must keep (agent_service depends on it):
#   sectors()            -> list of sector ids, e.g. ["A1", "A2", ...]
#   detections(sector)   -> list of {"kind": str, "confidence": float in (0, 1],
#                                    "pos": [x, y]}
#                           kind "person" is what the agent counts as a victim.
#   drone(drone_id)      -> {"battery": int %, "sector": str, "status": str}
#   weather(sector)      -> str, e.g. "clear", "smoke", "wind"
# Return None for an unknown sector or drone; the endpoint turns that into a
# 404, which the agent's tool loop shows to the model as an error.
# ---------------------------------------------------------------------------


class MockSource:
    """Fixed example data for six sectors and three drones (the tutorial world)."""

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

    def sectors(self):
        return list(self.SECTORS)

    def detections(self, sector):
        return self.DETECTIONS.get(sector)

    def drone(self, drone_id):
        return self.DRONES.get(drone_id)

    def weather(self, sector):
        return self.WEATHER.get(sector)


class RealSource:
    """Connect to your real detection system here.

    Fill in each method so it returns the same shapes as MockSource (see the
    contract above), then run with DETECTION_SOURCE=real. Any method left
    unimplemented returns HTTP 501 from its endpoint.
    """

    def __init__(self):
        # TODO: set up connections, e.g.
        #   self.api = os.environ["DETECTOR_API_URL"]      # detector results API
        #   self.fleet = os.environ["FLEET_API_URL"]       # drone telemetry
        #   self.weather_api = os.environ["WEATHER_API_URL"]
        pass

    def sectors(self):
        # TODO: return the sector ids of the search area, e.g.
        #   return requests.get(f"{self.api}/sectors", timeout=5).json()
        raise NotImplementedError("RealSource.sectors")

    def detections(self, sector):
        # TODO: return the latest detections for `sector` from the on-board
        # detector (e.g. an object-detection model on the drone), mapped to
        #   [{"kind": "person", "confidence": 0.91, "pos": [x, y]}, ...]
        # Example:
        #   resp = requests.get(f"{self.api}/detections",
        #                       params={"sector": sector}, timeout=5)
        #   if resp.status_code == 404:
        #       return None
        #   return [{"kind": d["label"], "confidence": d["score"],
        #            "pos": [d["x"], d["y"]]} for d in resp.json()]
        raise NotImplementedError("RealSource.detections")

    def drone(self, drone_id):
        # TODO: return {"battery": ..., "sector": ..., "status": ...} from
        # the drone fleet / telemetry system, or None if the id is unknown.
        raise NotImplementedError("RealSource.drone")

    def weather(self, sector):
        # TODO: return the current conditions for `sector` as a short string
        # ("clear", "smoke", "wind", ...), or None if the sector is unknown.
        raise NotImplementedError("RealSource.weather")


SOURCES = {"mock": MockSource, "real": RealSource}
if DETECTION_SOURCE not in SOURCES:
    raise RuntimeError(f"DETECTION_SOURCE must be one of {sorted(SOURCES)}, "
                       f"got {DETECTION_SOURCE!r}")
source = SOURCES[DETECTION_SOURCE]()


def call_source(method, *args):
    """Call a source method; an unimplemented method becomes HTTP 501."""
    try:
        return getattr(source, method)(*args)
    except NotImplementedError as exc:
        raise HTTPException(501, f"{exc} is not implemented yet "
                                 f"(DETECTION_SOURCE={DETECTION_SOURCE})")


# FastAPI app
app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())
FastAPIInstrumentor.instrument_app(app)


@app.get("/sectors")
def list_sectors():
    detection_counter.add(1)
    with tracer.start_as_current_span("list_sectors"):
        return {"sectors": call_source("sectors")}


@app.get("/detections/{sector}")
def get_detections(sector: str):
    detection_counter.add(1)
    with tracer.start_as_current_span("get_detections") as span:
        span.set_attribute("sector", sector)
        detections = call_source("detections", sector)
        if detections is None:
            raise HTTPException(404, f"unknown sector {sector!r}")
        return {"sector": sector, "detections": detections}


@app.get("/drones/{drone_id}")
def get_drone(drone_id: int):
    detection_counter.add(1)
    with tracer.start_as_current_span("drone_status") as span:
        span.set_attribute("drone.id", drone_id)
        drone = call_source("drone", drone_id)
        if drone is None:
            raise HTTPException(404, f"unknown drone {drone_id!r}")
        return {"drone_id": drone_id, **drone}


@app.get("/weather/{sector}")
def get_weather(sector: str):
    detection_counter.add(1)
    with tracer.start_as_current_span("get_weather") as span:
        span.set_attribute("sector", sector)
        conditions = call_source("weather", sector)
        if conditions is None:
            raise HTTPException(404, f"unknown sector {sector!r}")
        return {"sector": sector, "conditions": conditions}
