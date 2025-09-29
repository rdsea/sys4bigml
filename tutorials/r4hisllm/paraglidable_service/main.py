# FASTAPI imports
from fastapi import FastAPI, HTTPException
import datetime, os
from dotenv import load_dotenv

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
import aiohttp
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
AioHttpClientInstrumentor().instrument()

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
async def get_spots():
    # Increment Prometheus counter
    spots_counter.add(1)

    with tracer.start_as_current_span("get_spots") as fetch_span:
        fetch_span.set_attribute("interaction_type", "S2S")  # Service-to-Service
        now = datetime.datetime.now()

        if CACHE["data"] and CACHE["timestamp"]:
            if (now - CACHE["timestamp"]).seconds < CACHE_TTL_SECONDS:
                return {"spots": CACHE["data"]}

        url = f"https://api.paraglidable.com/?key={PARAGLIDABLE_KEY}&format=JSON"
        try:
            with tracer.start_as_current_span("fetch_external_api") as api_span:
                api_span.set_attribute("interaction_type", "S2S")  # external API fetch as service call
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            raise HTTPException(status_code=503, detail="Failed to fetch spots")
                        data = await resp.json()

                # If response is a dict with "spots"
                        if isinstance(data, dict) and "spots" in data:
                            api_data = data["spots"]
                        else:
                            api_data = data  # fallback if it's already a list

                        all_spots = []

                        if isinstance(api_data, dict):
                            # case: dict of {date: [spots]}
                            for date, spots in api_data.items():
                                for s in spots:
                                    all_spots.append({
                                        "name": s.get("name"),
                                        "lat": s.get("lat"),
                                        "lon": s.get("lon"),
                                        "forecast": s.get("forecast"),
                                        "date": date
                                    })

                        elif isinstance(api_data, list):
                            # case: already a list of spots
                            for s in api_data:
                                all_spots.append({
                                    "name": s.get("name"),
                                    "lat": s.get("lat"),
                                    "lon": s.get("lon"),
                                    "forecast": s.get("forecast"),
                                    "date": s.get("date")  # might already exist in the item
                                })
                        else:
                            raise HTTPException(status_code=500, detail=f"Unexpected API format: {type(api_data)}")

            CACHE["data"] = all_spots
            CACHE["timestamp"] = now
            return {"spots": all_spots}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching spots: {e}")