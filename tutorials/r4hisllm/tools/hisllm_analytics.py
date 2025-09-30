# make sure you setup CLICKHOUSE_TRACE_URL
# CLICKHOUSE_TRACE_URL clickhouse://default:changeme@130.233.195.221:8123/otel
import argparse
import asyncio
from collections import defaultdict
import os
from random import choice
from urllib.parse import urlparse
from tabulate import tabulate
import clickhouse_connect  # pip install clickhouse-connect

INTERACTION_TYPES = ["S2S", "H2S", "H2H"]

# --- ClickHouse fetch function --- #
def fetch_traces(service_name: str, client, limit: int = 50):
    """
    Fetch traces for a service from ClickHouse using Jaeger's schema.
    """
    query = f"""
        SELECT traceID, spanID, operationName, serviceName, startTime, duration, tags
        FROM jaeger_spans
        WHERE serviceName = '{service_name}'
        ORDER BY startTime DESC
        LIMIT {limit}
    """
    result = client.query(query)
    rows = result.result_rows
    traces = []
    for row in rows:
        trace_dict = {
            "spans": [
                {
                    "operationName": row[2],
                    "process": {"serviceName": row[3]},
                    # Jaeger durations are in microseconds
                    "duration": row[5],
                    "tags": [{"key": k, "value": v} for k, v in parse_tags(row[6]).items()],
                }
            ]
        }
        traces.append(trace_dict)
    return traces


def parse_tags(tags_str):
    """Parse tags from JSON or key=value format"""
    if not tags_str:
        return {}
    tags = {}
    import json
    tags_str = tags_str.strip()
    if tags_str.startswith("{") and tags_str.endswith("}"):
        try:
            tags = json.loads(tags_str)
        except:
            pass
    elif "=" in tags_str:
        for kv in tags_str.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                tags[k.strip()] = v.strip()
    return tags


# --- Keep all processing functions the same --- #
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


async def get_all_interactions(service_names, client):
    results = {}
    for svc in service_names:
        traces = fetch_traces(svc, client)
        results[svc] = process_traces(traces)
    return results


async def get_interaction_summary(service_names, client):
    total_summary = {itype: {"count": 0, "total_duration_ms": 0.0} for itype in INTERACTION_TYPES}
    for svc in service_names:
        traces = fetch_traces(svc, client)
        svc_summary = process_traces(traces)
        for itype, stats in svc_summary.items():
            total_summary[itype]["count"] += stats["count"]
            total_summary[itype]["total_duration_ms"] += stats["avg_duration_ms"] * stats["count"]

    for itype, stats in total_summary.items():
        count = stats["count"]
        stats["avg_duration_ms"] = stats["total_duration_ms"] / count if count else 0.0
        stats.pop("total_duration_ms")
    return total_summary


async def get_interaction_counts(service_names, client):
    counts = defaultdict(lambda: defaultdict(int))
    for svc in service_names:
        traces = fetch_traces(svc, client)
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


async def get_trace_table(service_names, client):
    agg = defaultdict(lambda: {"count": 0, "total_duration_ms": 0.0})
    for svc in service_names:
        traces = fetch_traces(svc, client)
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
    parser = argparse.ArgumentParser(description="Observability Analysis CLI (ClickHouse)")
    parser.add_argument("--services", required=True, help="Comma-separated service names")
    parser.add_argument(
        "--feature",
        required=True,
        choices=["perservice_interactions", "summary_interactions", "interaction_counts", "detailed_trace_table"],
        help="Feature to run"
    )
    args = parser.parse_args()
    # make sure you have the right environment setting
    click_house_url = os.environ['CLICKHOUSE_TRACE_URL']
    click_house_info = urlparse(click_house_url)
    # remove the first / to have the database name
    print(f'Connect to the db={click_house_info.path[1:]}')
    client = clickhouse_connect.get_client(
        host= click_house_info.hostname,
        port= click_house_info.port,
        username=click_house_info.username,
        password=click_house_info.password,
        database=click_house_info.path[1:],
    )

    services = [s.strip() for s in args.services.split(",")]

    if args.feature == "perservice_interactions":
        result = await get_all_interactions(services, client)
        print("\nPer-service interaction summary:")
        for svc, summary in result.items():
            table = [[itype, stats["count"], round(stats["avg_duration_ms"], 3)] for itype, stats in summary.items()]
            print(f"\nService: {svc}")
            print(tabulate(table, headers=["Interaction Type", "Count", "Avg Duration (ms)"], tablefmt="grid"))

    elif args.feature == "summary_interactions":
        result = await get_interaction_summary(services, client)
        table = [[itype, stats["count"], round(stats["avg_duration_ms"], 3)] for itype, stats in result.items()]
        print("\nAggregated interaction summary:")
        print(tabulate(table, headers=["Interaction Type", "Count", "Avg Duration (ms)"], tablefmt="grid"))

    elif args.feature == "interaction_counts":
        result = await get_interaction_counts(services, client)
        print("\nInteraction counts (caller -> callee):")
        print(tabulate(result, headers=["Caller Service", "Callee Service", "Count"], tablefmt="grid"))

    elif args.feature == "detailed_trace_table":
        result = await get_trace_table(services, client)
        print("\nDetailed trace table:")
        print(tabulate(result, headers=["Caller", "Input", "Callee", "Output", "Count", "Avg Duration (ms)"], tablefmt="grid"))


if __name__ == "__main__":
    asyncio.run(main())
