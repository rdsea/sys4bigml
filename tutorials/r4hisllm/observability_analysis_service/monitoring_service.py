# monitoring_service.py
from fastapi import FastAPI, HTTPException
import aiohttp
import os
from collections import defaultdict

app = FastAPI(title="HIS-LLM Interaction Monitor")

JAEGER_API = os.getenv("JAEGER_API", "http://host.docker.internal:16686/api/traces")

# --- Fetch traces ---
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

# --- Build pairwise interaction table ---
def process_interactions(traces):
    edge_counts = defaultdict(int)

    for trace in traces:
        processes = trace.get("processes", {})
        process_map = {pid: p.get("serviceName") for pid, p in processes.items()}

        for span in trace.get("spans", []):
            service_name = process_map.get(span.get("processID"))
            parent_refs = span.get("references", [])

            # If span has a parent, link services
            for ref in parent_refs:
                parent_span_id = ref.get("spanID")
                # find parent span’s service
                parent_service = None
                for s in trace.get("spans", []):
                    if s.get("spanID") == parent_span_id:
                        parent_service = process_map.get(s.get("processID"))
                        break

                if parent_service and service_name:
                    edge_counts[(parent_service, service_name)] += 1

    # Convert to table
    table = []
    for (svc1, svc2), count in edge_counts.items():
        table.append({
            "Service_1": svc1,
            "Service_2": svc2,
            "Interaction_Counts": count
        })
    return table

# --- API endpoint ---
@app.get("/interaction-table")
async def get_interaction_table(services: str = "", limit: int = 50):
    """
    Example:
    /interaction-table?services=agent_service,human_service,paraglidable_service
    """
    if not services:
        raise HTTPException(status_code=400, detail="Please provide at least one service name")
    
    service_list = [s.strip() for s in services.split(",")]
    all_traces = []
    for svc in service_list:
        traces = await fetch_traces(svc, limit)
        all_traces.extend(traces)

    table = process_interactions(all_traces)
    return {"interaction_table": table}
