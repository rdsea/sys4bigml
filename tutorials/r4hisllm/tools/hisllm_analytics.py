import aiohttp
import argparse
import asyncio
from collections import defaultdict
from tabulate import tabulate 

INTERACTION_TYPES = ["S2S", "H2S", "H2H"]

async def fetch_traces(service_name: str, jaeger_api: str, limit: int = 50):
    params = {"service": service_name, "limit": limit}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(jaeger_api, params=params) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to fetch traces for {service_name}: {await resp.text()}")
                data = await resp.json()
                return data.get("data", [])
        except Exception as e:
            raise Exception(f"Error fetching traces for {service_name}: {e}")

def process_traces(traces):
    summary = {itype: {"count": 0, "total_duration_ms": 0.0} for itype in INTERACTION_TYPES}
    for trace in traces:
        for span in trace.get("spans", []):
            tags_list = span.get("tags", [])
            tags = {tag.get("key"): tag.get("value") for tag in tags_list if "key" in tag and "value" in tag}
            itype = tags.get("interaction_type", "Unknown")
            if itype in INTERACTION_TYPES:
                summary[itype]["count"] += 1
                duration_ms = span.get("duration", 0) / 1e6
                summary[itype]["total_duration_ms"] += duration_ms

    for itype, stats in summary.items():
        count = stats["count"]
        stats["avg_duration_ms"] = stats["total_duration_ms"] / count if count else 0.0
        stats.pop("total_duration_ms")
    return summary

async def get_all_interactions(service_names, jaeger_api):
    results = {}
    for svc in service_names:
        traces = await fetch_traces(svc, jaeger_api)
        results[svc] = process_traces(traces)
    return results

async def get_interaction_summary(service_names, jaeger_api):
    total_summary = {itype: {"count": 0, "total_duration_ms": 0.0} for itype in INTERACTION_TYPES}
    for svc in service_names:
        traces = await fetch_traces(svc, jaeger_api)
        svc_summary = process_traces(traces)
        for itype, stats in svc_summary.items():
            total_summary[itype]["count"] += stats["count"]
            total_summary[itype]["total_duration_ms"] += stats["avg_duration_ms"] * stats["count"]

    for itype, stats in total_summary.items():
        count = stats["count"]
        stats["avg_duration_ms"] = stats["total_duration_ms"] / count if count else 0.0
        stats.pop("total_duration_ms")
    return total_summary

async def get_interaction_counts(service_names, jaeger_api):
    counts = defaultdict(lambda: defaultdict(int))
    for svc in service_names:
        traces = await fetch_traces(svc, jaeger_api)
        for trace in traces:
            for span in trace.get("spans", []):
                tags_list = span.get("tags", [])
                tags = {tag.get("key"): tag.get("value") for tag in tags_list if "key" in tag and "value" in tag}
                caller = tags.get("caller_service") or span.get("process", {}).get("serviceName") or svc
                callee = tags.get("callee_service") or span.get("operationName") or "Unknown"
                counts[caller][callee] += 1

    table = []
    for caller, callees in counts.items():
        for callee, count in callees.items():
            table.append([caller, callee, count])
    table.sort(key=lambda x: (x[0], x[1]))
    return table

async def get_trace_table(service_names, jaeger_api):
    agg = defaultdict(lambda: {"count": 0, "total_duration_ms": 0.0})
    for svc in service_names:
        traces = await fetch_traces(svc, jaeger_api)
        for trace in traces:
            for span in trace.get("spans", []):
                tags_list = span.get("tags", [])
                tags = {tag.get("key"): tag.get("value") for tag in tags_list if "key" in tag and "value" in tag}
                caller = tags.get("caller_service") or span.get("process", {}).get("serviceName") or svc
                callee = tags.get("callee_service") or span.get("operationName") or "Unknown"
                input_data = tags.get("input") or "Unknown"
                output_data = tags.get("output") or "Unknown"
                duration_ms = span.get("duration", 0) / 1000
                key = (caller, input_data, callee, output_data)
                agg[key]["count"] += 1
                agg[key]["total_duration_ms"] += duration_ms

    table = []
    for (caller, input_data, callee, output_data), stats in agg.items():
        avg_duration = stats["total_duration_ms"] / stats["count"] if stats["count"] else 0.0
        table.append([caller, input_data, callee, output_data, stats["count"], round(avg_duration, 3)])

    table.sort(key=lambda x: (x[0], x[2], x[1]))
    return table

async def main():
    parser = argparse.ArgumentParser(description="Observability Analysis CLI (Jaeger API)")
    parser.add_argument("--services", required=True, help="Comma-separated service names")
    parser.add_argument("--jaeger-api", required=True, help="Full Jaeger query API URL, e.g., http://localhost:16686/api/traces")
    parser.add_argument(
        "--feature",
        required=True,
        choices=["perservice_interactions", "summary_interactions", "interaction_counts", "detailed_trace_table"],
        help="Feature to run"
    )
    args = parser.parse_args()
    services = [s.strip() for s in args.services.split(",")]

    if args.feature == "perservice_interactions":
        result = await get_all_interactions(services, args.jaeger_api)
        print("\nPer-service interaction summary:")
        for svc, summary in result.items():
            table = [[itype, stats["count"], round(stats["avg_duration_ms"], 3)] for itype, stats in summary.items()]
            print(f"\nService: {svc}")
            print(tabulate(table, headers=["Interaction Type", "Count", "Avg Duration (ms)"], tablefmt="grid"))

    elif args.feature == "summary_interactions":
        result = await get_interaction_summary(services, args.jaeger_api)
        table = [[itype, stats["count"], round(stats["avg_duration_ms"], 3)] for itype, stats in result.items()]
        print("\nAggregated interaction summary:")
        print(tabulate(table, headers=["Interaction Type", "Count", "Avg Duration (ms)"], tablefmt="grid"))

    elif args.feature == "interaction_counts":
        result = await get_interaction_counts(services, args.jaeger_api)
        print("\nInteraction counts (caller -> callee):")
        print(tabulate(result, headers=["Caller Service", "Callee Service", "Count"], tablefmt="grid"))

    elif args.feature == "detailed_trace_table":
        result = await get_trace_table(services, args.jaeger_api)
        print("\nDetailed trace table:")
        print(tabulate(result, headers=["Caller", "Input", "Callee", "Output", "Count", "Avg Duration (ms)"], tablefmt="grid"))

if __name__ == "__main__":
    asyncio.run(main())
