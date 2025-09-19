# FASTAPI imports
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Dotenv for environment variables
import os
from dotenv import load_dotenv
# LangChain imports
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import StrOutputParser
# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
# Prometheus metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider, Counter
# Mount /metrics endpoint
from starlette.middleware.wsgi import WSGIMiddleware
from prometheus_client import make_asgi_app
# Opik for LLM tracing
import opik
from opik.integrations.langchain import OpikTracer
# Load environment variables
load_dotenv()
# Ollama environment variables
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT"))
# OTEL environment variables
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT_HTTP")
SERVICE_NAME = os.getenv("AGENT_OTEL_SERVICE_NAME")
# --------------------------
# OpenTelemetry Tracing Setup
# --------------------------
resource = Resource(attributes={"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT))
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)
# --------------------------
# OpenTelemetry Metrics Setup
# --------------------------
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(SERVICE_NAME)

# Create example metrics
request_counter = meter.create_counter(
    "agent_requests_total",
    description="Total requests handled by the agent service"
)

llm_request_counter = meter.create_counter(
    "agent_llm_requests_total",
    description="Total LLM calls from agent service"
)

external_service_counter = meter.create_counter(
    "agent_external_requests_total",
    description="Total requests to external services"
)
# Create the Opik tracer
opik.configure(use_local=True)
opik_tracer = OpikTracer(tags=["langchain", "ollama"])
# --------------------------
# FastAPI app setup
# --------------------------
app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())

# Instrument FastAPI and requests
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

# Enable CORS for frontend
origins = [
    "http://localhost:3100",
    "http://127.0.0.1:3100",
    "http://frontend_service:80",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
PARAGLIDABLE_SERVICE_URL = os.getenv("PARAGLIDABLE_SERVICE_API_URL")
HUMAN_SERVICE_URL = os.getenv("HUMAN_SERVICE_API_URL")

# Initialize OllamaLLM
llm = OllamaLLM(
    model=OLLAMA_MODEL,
    temperature=0.7,
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
).with_config({"callbacks": [opik_tracer]})

@app.get("/greet")
def greet_user():
    request_counter.add(1)  # Increment metric
    with tracer.start_as_current_span("greet_user"):
        try:
            # Fetch spots
            resp = requests.get(PARAGLIDABLE_SERVICE_URL, timeout=5)
            external_service_counter.add(1)  # Increment metric
            resp.raise_for_status()
            spots = resp.json().get("spots", [])
            spot_names = [s['name'] for s in spots]
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to fetch spots: {e}")

        try:
            # Step 1: Ask LLM for city
            city_prompt = PromptTemplate(
                template="Given the spots: {spots}, what is the city they belong to? Only respond with the city name.",
                input_variables=["spots"]
            )
            output_parser = StrOutputParser()
            chain_city = RunnableSequence(city_prompt | llm | output_parser)
            llm_request_counter.add(1)  # Increment metric
            city = chain_city.invoke({"spots": spot_names})

            # Step 2: Generate friendly greeting mentioning the city
            greeting_prompt = PromptTemplate(
                template="Generate a friendly greeting for a user who will go to paragliding there and mention that the spots are available in {city}. Keep it short.",
                input_variables=["city"]
            )
            chain_greeting = RunnableSequence(greeting_prompt | llm | output_parser)
            greeting = chain_greeting.invoke({"city": city.strip()})

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM processing error: {e}")

        return {"message": greeting}

@app.post("/plan")
def plan_paragliding(user_input: dict):
    request_counter.add(1)  # Increment metric
    with tracer.start_as_current_span("plan_paragliding"):
        try:
            # 1. Fetch spots from paraglidable_service
            resp = requests.get(PARAGLIDABLE_SERVICE_URL, timeout=5)
            external_service_counter.add(1)  # Increment metric
            resp.raise_for_status()
            spots = resp.json().get("spots", [])
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Failed to fetch spots: {e}")

        # 2. Build spots text with forecast info
        spots_info = []
        for s in spots:
            spot_str = (
                f"{s['name']} (fly: {s['forecast']['fly']:.2f}, "
                f"XC: {s['forecast']['XC']:.2f}, "
                f"takeoff: {s['forecast']['takeoff']:.2f}, "
                f"date: {s['date']})"
            )
            spots_info.append(spot_str)
        spots_text = "; ".join(spots_info)

        # 3. Ask LLM to suggest top spots
        prompt_llm = PromptTemplate(
            input_variables=["user_input", "spots_text"],
            template=(
                "User wants to plan: {user_input}. "
                "Available spots with forecasts: {spots_text}. "
                "Suggest the top 3 spots for paragliding based on 'fly' and 'XC' probabilities."
            )
        )
        chain_llm = RunnableSequence(prompt_llm | llm | StrOutputParser())
        llm_request_counter.add(1)  # Increment metric
        llm_suggestion = chain_llm.invoke({
            "user_input": user_input.get("query", ""),
            "spots_text": spots_text
        })

        # 4. Ask human review service to validate/refine the suggestion
        try:
            review_response = requests.post(
                HUMAN_SERVICE_URL,
                json={"llm_suggestion": llm_suggestion},
                timeout=5
            )
            external_service_counter.add(1)  # Increment metric
            review_response.raise_for_status()
            expert_review = review_response.json()
        except Exception as e:
            expert_review = {"error": f"Human review service unavailable: {e}"}

        # 5. Aggregate results into a final explanation chain
        prompt_summary = PromptTemplate(
            input_variables=["llm_suggestion", "expert_review"],
            template=(
                "We followed this process:\n"
                "1. Fetched forecast data for all spots.\n"
                "2. Generated initial LLM suggestion for top paragliding spots.\n"
                "3. Sent the suggestion to an expert review service.\n\n"
                "LLM suggestion:\n{llm_suggestion}\n\n"
                "Expert review:\n{expert_review}\n\n"
                "Now please provide the final recommended spots summary for the user, "
                "integrating both LLM and expert inputs."
            )
        )
        chain_summary = RunnableSequence(prompt_summary | llm | StrOutputParser())
        llm_request_counter.add(1)  # Increment metric
        final_result = chain_summary.invoke({
            "llm_suggestion": llm_suggestion,
            "expert_review": expert_review
        })

        # 6. Compute final decision from expert votes
        final_decision = "undecided"
        if isinstance(expert_review, dict) and "votes" in expert_review:
            votes = [v.get("vote") for v in expert_review["votes"] if "vote" in v]
            if votes:
                approve_count = votes.count("approve")
                reject_count = votes.count("reject")
                if approve_count > reject_count:
                    final_decision = "approved"
                elif reject_count > approve_count:
                    final_decision = "rejected"
                else:
                    final_decision = "tie"

        return {
            "llm_suggestion": llm_suggestion,
            "expert_review": expert_review,
            "final_result": final_result,
            "finalDecision": final_decision
        }
