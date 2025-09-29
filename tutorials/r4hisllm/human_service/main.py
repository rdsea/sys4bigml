# FastAPI imports
from fastapi import FastAPI
import random
import os
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
SERVICE_NAME = os.getenv("HUMAN_OTEL_SERVICE_NAME")

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

# Define a counter for review requests
review_counter = meter.create_counter(
    name="human_review_requests_total",
    description="Total number of human review requests",
    unit="1"
)

# FastAPI app
app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())

# Instrument FastAPI and requests
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

@app.post("/review")
def review_spots(data: dict):
    # Increment Prometheus counter
    review_counter.add(1)

    with tracer.start_as_current_span("review_spots") as root_span:
        root_span.set_attribute("interaction_type", "H2H")  # Human-to-Human via service
        suggestions = data.get("llm_suggestion", "")
        experts = ["expert1", "expert2", "expert3"]
        votes = []

        for e in experts:
            with tracer.start_as_current_span(f"vote_by_{e}") as vote_span:
                # Mark this sub-span as H2H as well
                vote_span.set_attribute("interaction_type", "H2H")
                vote_span.set_attribute("expert", e)

                # Simulate voting logic
                vote = random.choice(["approve", "reject"])
                comment = f"{e} says: {vote} for suggestion."
                votes.append({"expert": e, "vote": vote, "comment": comment})

        return {"votes": votes}
