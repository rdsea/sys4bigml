# monitoring_service.py
from fastapi import FastAPI, HTTPException
import aiohttp
import os

app = FastAPI(title="HIS-LLM Interaction Monitor")

JAEGER_API = os.getenv("JAEGER_API", "http://host.docker.internal:16686/api/traces")
INTERACTION_TYPES = ["S2S", "H2S", "H2H"]

# Fetch traces from Jaeger for a single service
async def fetch_traces(service_name: str, limit: int = 50):
    params = {"service": service_name, "limit": limit}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(JAEGER_API, params=params) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail=f"Failed to fetch traces for {service_name}")
                data = await resp.json()
                return data.get("data", [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching traces for {service_name}: {e}")

# Process spans and group by interaction_type
def process_traces(traces):
    summary = {itype: {"count": 0, "total_duration_ms": 0.0} for itype in INTERACTION_TYPES}
    for trace in traces:
        for span in trace.get("spans", []):
            tags_list = span.get("tags", [])
            tags = {tag.get("key"): tag.get("value") for tag in tags_list if "key" in tag and "value" in tag}
            itype = tags.get("interaction_type", "Unknown")
            if itype in INTERACTION_TYPES:
                summary[itype]["count"] += 1
                duration_ms = span.get("duration", 0) / 1e6  # ns → ms
                summary[itype]["total_duration_ms"] += duration_ms
    # Compute average duration
    for itype, stats in summary.items():
        count = stats["count"]
        stats["avg_duration_ms"] = stats["total_duration_ms"] / count if count else 0.0
        stats.pop("total_duration_ms")
    return summary

# Fetch and summarize multiple services at once
@app.get("/interactions")
async def get_all_interactions(services: str = ""):
    """
    Query multiple services as a comma-separated list:
    /interactions?services=agent_service,human_service,paraglidable_service
    """
    if not services:
        raise HTTPException(status_code=400, detail="Please provide at least one service name")
    
    service_list = [s.strip() for s in services.split(",")]
    results = {}

    for svc in service_list:
        traces = await fetch_traces(svc)
        results[svc] = process_traces(traces)

    return {"interaction_summary": results}
