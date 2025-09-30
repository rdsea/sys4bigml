# monitoring_service.py
from fastapi import FastAPI, HTTPException
from collections import defaultdict
import aiohttp
import os

app = FastAPI(title="HIS-LLM Interaction Monitor")

JAEGER_API = os.getenv("JAEGER_API")
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

@app.get("/interactions/summary")
async def get_interaction_summary(services: str = ""):
    """
    Aggregate interactions across multiple services.
    Example:
    /interactions/summary?services=agent_service,human_service,paraglidable_service
    """
    if not services:
        raise HTTPException(status_code=400, detail="Please provide at least one service name")
    
    service_list = [s.strip() for s in services.split(",")]
    
    # Initialize total summary
    total_summary = {itype: {"count": 0, "total_duration_ms": 0.0} for itype in INTERACTION_TYPES}

    # Fetch and accumulate traces
    for svc in service_list:
        traces = await fetch_traces(svc)
        svc_summary = process_traces(traces)
        for itype, stats in svc_summary.items():
            total_summary[itype]["count"] += stats["count"]
            total_summary[itype]["total_duration_ms"] += stats.get("avg_duration_ms", 0.0) * stats["count"]

    # Compute aggregated average duration
    for itype, stats in total_summary.items():
        count = stats["count"]
        stats["avg_duration_ms"] = stats["total_duration_ms"] / count if count else 0.0
        stats.pop("total_duration_ms")

    return {"aggregated_interaction_summary": total_summary}

from collections import defaultdict

@app.get("/interactions/counts")
async def get_interaction_counts(services: str = ""):
    """
    Returns a hierarchical table-like summary:
    caller_service | callee_service | count
    Aggregates all interactions across requested services.
    Example:
    /interactions/counts?services=agent_service,human_service
    """
    if not services:
        raise HTTPException(status_code=400, detail="Please provide at least one service name")

    service_list = [s.strip() for s in services.split(",")]

    # Nested dict: caller -> callee -> count
    counts = defaultdict(lambda: defaultdict(int))

    for svc in service_list:
        traces = await fetch_traces(svc)
        for trace in traces:
            for span in trace.get("spans", []):
                tags_list = span.get("tags", [])
                tags = {tag.get("key"): tag.get("value") for tag in tags_list if "key" in tag and "value" in tag}

                caller = tags.get("caller_service") or span.get("process", {}).get("serviceName") or svc
                callee = tags.get("callee_service") or span.get("operationName") or "Unknown"

                counts[caller][callee] += 1

    # Flatten into table-like list
    table = []
    for caller, callees in counts.items():
        for callee, count in callees.items():
            table.append({
                "caller_service": caller,
                "callee_service": callee,
                "count": count
            })

    # Optional: sort by caller -> callee
    table.sort(key=lambda x: (x["caller_service"], x["callee_service"]))

    return {"service_call_counts": table}

@app.get("/interactions/trace_table")
async def get_trace_table(services: str = ""):
    """
    Returns a table of interactions:
    Caller | Input | Callee | Output | avg_duration_ms
    Aggregates multiple spans between the same caller and callee.
    Example:
    /interactions/trace_table?services=agent_service,human_service
    """
    if not services:
        raise HTTPException(status_code=400, detail="Please provide at least one service name")

    service_list = [s.strip() for s in services.split(",")]

    # Use a dict to accumulate total duration and count per caller-callee-input-output
    agg = defaultdict(lambda: {"count": 0, "total_duration_ms": 0.0})

    raw_entries = []

    for svc in service_list:
        traces = await fetch_traces(svc)
        for trace in traces:
            for span in trace.get("spans", []):
                tags_list = span.get("tags", [])
                tags = {tag.get("key"): tag.get("value") for tag in tags_list if "key" in tag and "value" in tag}

                caller = tags.get("caller_service") or span.get("process", {}).get("serviceName") or svc
                callee = tags.get("callee_service") or span.get("operationName") or "Unknown"
                input_data = tags.get("input") or "Unknown"
                output_data = tags.get("output") or "Unknown"
                duration_ms = span.get("duration", 0) / 1000  # μs → ms

                # Use tuple key to aggregate
                key = (caller, input_data, callee, output_data)
                agg[key]["count"] += 1
                agg[key]["total_duration_ms"] += duration_ms

                # Keep raw entries (optional, for non-aggregated table)
                raw_entries.append({
                    "caller": caller,
                    "input": input_data,
                    "callee": callee,
                    "output": output_data,
                    "duration_ms": duration_ms
                })

    # Build final aggregated table
    table = []
    for (caller, input_data, callee, output_data), stats in agg.items():
        avg_duration = stats["total_duration_ms"] / stats["count"] if stats["count"] else 0.0
        table.append({
            "caller": caller,
            "input": input_data,
            "callee": callee,
            "output": output_data,
            "count": stats["count"],
            "avg_duration_ms": avg_duration
        })

    # Optional: sort table
    table.sort(key=lambda x: (x["caller"], x["callee"], x["input"]))

    return {"trace_table": table}