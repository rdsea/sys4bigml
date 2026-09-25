#!/usr/bin/env python3
"""Analyze HIS-LLM interactions from Jaeger traces.

Fetches spans from Jaeger and reports:
  - interaction counts (S2S:ai_to_llm, S2S:ai_to_service, S2S, H2S, H2H)
  - LLM reliability (retries, calls per task)
  - human reviews (decisions, latency)
  - the effect of each pattern configuration

Interaction types are worked out from the spans (see ``derive_interaction``),
not tagged in the services.

Examples:

    python3 mission_analytics.py --feature=summary_interactions
    python3 mission_analytics.py --feature=pattern_effect
    python3 mission_analytics.py --feature=llm_reliability

    # only include runs with one pattern configuration
    python3 mission_analytics.py --feature=summary_interactions --patterns=all
    python3 mission_analytics.py --feature=summary_interactions \
        --patterns=structured+dispatcher+routing+parallel
    python3 mission_analytics.py --services=agent_service,human_service \
        --jaeger-api=http://localhost:16686/api/traces --feature=human_reviews
"""
import argparse
from collections import Counter, defaultdict

import requests


def fetch_spans(jaeger_api, services, limit=200):
    """Return all spans from the last `limit` traces of each service.

    - Jaeger returns a shared trace once per service, so spans are
      de-duplicated by (traceID, spanID).
    - Each span gets a `_service` field with its service name.
    """
    spans, seen = [], set()
    for service in services:
        resp = requests.get(jaeger_api, params={"service": service,
                                                "limit": limit}, timeout=15)
        resp.raise_for_status()
        for trace in resp.json().get("data", []):
            processes = trace.get("processes", {})
            for span in trace.get("spans", []):
                key = (trace.get("traceID"), span.get("spanID"))
                if key in seen:
                    continue
                seen.add(key)
                process = processes.get(span.get("processID"), {})
                span["_service"] = process.get("serviceName",
                                               span.get("processID", "?"))
                spans.append(span)
    return spans


def scope_to_patterns(spans, config):
    """Keep only traces whose `run.patterns` tag equals `config`.

    The tag is only on the root span, so we find matching trace IDs first
    and then keep every span in those traces.
    """
    wanted = {s.get("traceID") for s in spans
              if tag(s, "run.patterns") == config}
    return [s for s in spans if s.get("traceID") in wanted]


def tag(span, key, default=None):
    """Value of tag `key` on a Jaeger span, or `default`."""
    for t in span.get("tags", []):
        if t["key"] == key:
            return t["value"]
    return default


# ---------------------------------------------------------------------------
# Working out the interaction type of each span (no manual tags needed).
#
#   1. Between services: from a client HTTP span, use who made the call
#      (its service) and who received it (the child server span, or the URL).
#   2. Inside one service: from span names — `llm.complete` is a model call,
#      `vote_by_*` is an expert vote.
# If you rename those spans, update the constants below.
# ---------------------------------------------------------------------------

# Service name -> role.
ROLES = {"agent_service": "AI",       # an LLM-driven component
         "detection_service": "S",    # a plain software service
         "human_service": "H"}        # humans (the expert panel)

# Services that emit no spans (Ollama), recognised by URL. "L" = LLM.
PEER_ROLES = {"11434": "L",           # Ollama's port
              "/api/generate": "L",   # ...or its route, whichever matches
              "/v1/chat/completions": "L"}

# Span names used to detect in-service interactions.
LLM_SPAN = "llm.complete"             # one model call
VOTE_PREFIX = "vote_by_"              # one expert deliberating

# All interaction types. Every row is always shown, even when it is 0
# (bare S2S and H2H are always 0 in this system).
#
#   S2S  software <-> software (agents, LLMs, services)
#          ai_to_llm      agent <-> LLM
#          ai_to_service  agent <-> software service (e.g. detection_service)
#          (no sub-kind)  service <-> service, no agent involved
#   H2S  human <-> software (prompting, monitoring, feedback)
#   H2H  human <-> human, through a service
TAXONOMY = [("S2S", "ai_to_llm"),
            ("S2S", "ai_to_service"),
            ("S2S", None),
            ("H2S", None),
            ("H2H", None)]


def label(interaction):
    """("S2S", "ai_to_llm") -> "S2S:ai_to_llm"; ("H2S", None) -> "H2S"."""
    category, subkind = interaction
    return f"{category}:{subkind}" if subkind else category


def index_spans(spans):
    """Map (traceID, parent spanID) -> list of child spans."""
    children = defaultdict(list)
    for span in spans:
        for ref in span.get("references", []):
            if ref.get("refType") == "CHILD_OF":
                children[(ref.get("traceID"), ref.get("spanID"))].append(span)
    return children


def peer_role(span, children):
    """Role of the service this client span called, or None."""
    # Best: the called service's server span is a child of this span.
    for child in children.get((span.get("traceID"), span.get("spanID")), []):
        if child.get("_service") != span.get("_service"):
            return ROLES.get(child.get("_service"))
    # Otherwise (e.g. Ollama): match the URL.
    url = tag(span, "http.url", "") or ""
    for marker, role in PEER_ROLES.items():
        if marker in url:
            return role
    return None


def derive_interaction(span, children):
    """Return the span's interaction type as (category, sub-kind), or None.

    e.g. ("S2S", "ai_to_llm"), ("S2S", "ai_to_service"), ("H2S", None).
    H2H never occurs here: experts vote independently.
    """
    source = ROLES.get(span.get("_service"))
    if source is None:
        return None
    op = span.get("operationName", "")
    # -- inside one service: by span name --
    if op == LLM_SPAN and source == "AI":
        # Counted on llm.complete (not the HTTP call) so it also works for
        # models that don't make HTTP calls.
        return ("S2S", "ai_to_llm")
    if op.startswith(VOTE_PREFIX) and source == "H":
        # An expert's vote: human -> service.
        return ("H2S", None)
    # -- between services: by who called whom --
    if tag(span, "span.kind") == "client":
        target = peer_role(span, children)
        if target is None or target == "L":
            # Ollama calls are already counted on llm.complete.
            return None
        # Count on the client side only, so each call is counted once.
        if target == "H" or source == "H":
            return ("H2S", None)
        if target == "AI":
            # Agent -> another AI service. Always 0 here (only one agent).
            return ("S2S", "ai_to_llm")
        if source == "AI":
            # Agent -> software service.
            return ("S2S", "ai_to_service")
        # Service -> service, no agent: S2S with no sub-kind.
        return ("S2S", None)
    return None


def table(headers, rows):
    """Format rows as an ASCII table."""
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows
              else len(str(h)) for i, h in enumerate(headers)]
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    def fmt(cells):
        return "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"
    lines = [sep, fmt(headers), sep.replace("-", "=")]
    lines += [fmt(r) for r in rows]
    lines.append(sep)
    return "\n".join(lines)


def summary_interactions(spans):
    """Count and average duration for each interaction type."""
    children = index_spans(spans)
    stats = defaultdict(lambda: [0, 0.0])
    for s in spans:
        itype = derive_interaction(s, children)
        if itype:
            stats[itype][0] += 1
            stats[itype][1] += s.get("duration", 0) / 1000.0  # us -> ms
    print("Aggregated interaction summary:")
    rows = []
    for itype in TAXONOMY:
        n, total = stats.get(itype, (0, 0.0))
        rows.append([itype[0], itype[1] or "-", n,
                     f"{total / n:.3f}" if n else "-"])
    print(table(["Interaction", "Sub-kind", "Count", "Avg Duration (ms)"], rows))


def per_service_interactions(spans):
    """Interaction counts per service."""
    children = index_spans(spans)
    stats = Counter()
    for s in spans:
        itype = derive_interaction(s, children)
        if itype:
            proc = s.get("processID", "?")
            stats[(s.get("_service", proc), label(itype))] += 1
    print(table(["Service/Process", "Interaction", "Count"],
                [[svc, itype, n]
                 for (svc, itype), n in sorted(stats.items())]))


def llm_reliability(spans):
    """LLM call count, retry rate, and calls per task."""
    llm = [s for s in spans if s.get("operationName") == "llm.complete"]
    retries = [s for s in llm if str(tag(s, "llm.is_retry")).lower() == "true"]
    by_task = Counter(tag(s, "llm.task", "?") for s in llm)
    print(f"LLM calls: {len(llm)}   retries: {len(retries)}   "
          f"retry rate: {len(retries) / len(llm):.1%}" if llm
          else "no llm.complete spans found — run a mission first")
    if llm:
        print(table(["LLM Task", "Calls"],
                    [[t, n] for t, n in by_task.most_common()]))


def human_reviews(spans):
    """Human review decisions and expert decision latency."""
    reviews = [s for s in spans if s.get("operationName") == "review_victim_map"]
    votes = [s for s in spans if s.get("operationName", "").startswith("vote_by_")]
    rows = []
    for s in reviews:
        rows.append([tag(s, "decision", "?"),
                     f"{s.get('duration', 0) / 1000.0:.0f}",
                     tag(s, "reason", "")[:60]])
    print(f"human reviews: {len(reviews)}   expert votes: {len(votes)}")
    if votes:
        avg = sum(v.get("duration", 0) for v in votes) / len(votes) / 1000.0
        print(f"avg expert decision latency: {avg:.0f} ms")
    if rows:
        print(table(["Decision", "Panel Latency (ms)", "Reason"], rows))


def pattern_effect(spans):
    """One row per pattern configuration (`run.patterns` tag).

    Shows cost (LLM calls, retries, tool calls, time) and quality
    ("Errors shipped" = wrong values in the final map, compared with
    ground truth).
    """
    by_trace = defaultdict(list)
    for s in spans:
        by_trace[s.get("traceID")].append(s)

    rows, mixed = defaultdict(lambda: Counter()), 0
    for group in by_trace.values():
        configs = {tag(s, "run.patterns") for s in group
                   if tag(s, "run.patterns") is not None}
        if not configs:
            continue          # not a task trace (e.g. /greet)
        if len(configs) > 1:
            # A trace with two configurations can't be assigned to one row,
            # so skip it and report how many were skipped.
            mixed += 1
            continue
        config = configs.pop()
        r = rows[config]
        r["runs"] += 1
        r["llm"] += sum(1 for s in group
                        if s.get("operationName") == LLM_SPAN)
        r["retries"] += sum(1 for s in group
                            if str(tag(s, "llm.is_retry")).lower() == "true")
        r["tools"] += sum(1 for s in group
                          if s.get("operationName", "").startswith("tool."))
        r["human"] += sum(1 for s in group
                          if s.get("operationName") == "human.review")
        # Count aborted runs separately, so "0 errors because nothing
        # shipped" isn't mistaken for a correct map.
        shipped = next((tag(s, "score.shipped") for s in group
                        if tag(s, "score.shipped") is not None), None)
        if shipped is False or str(shipped).lower() == "false":
            r["nothing_shipped"] += 1
        errors = next((tag(s, "score.errors") for s in group
                       if tag(s, "score.errors") is not None), 0)
        r["errors"] += int(errors or 0)
        # Trace duration = its longest span (the root covers everything).
        r["ms"] += max((s.get("duration", 0) for s in group), default=0) / 1000.0

    if mixed:
        print(f"note: skipped {mixed} trace(s) carrying more than one pattern "
              f"configuration. Older /compare runs put both arms in one "
              f"trace; current ones give each arm its own.\n")
    if not rows:
        print("no runs carrying a run.patterns tag — run a task from the "
              "console or POST /mission first")
        return
    # Sort by number of patterns on: "none" first, "all" last.
    order = sorted(rows, key=lambda k: (0 if k == "none" else
                                        99 if k == "all" else k.count("+") + 1))
    print(table(["Patterns", "Runs", "LLM calls", "Retries", "Tool calls",
                 "Human gates", "Errors shipped", "Refused to ship", "Avg ms"],
                [[k, rows[k]["runs"], rows[k]["llm"], rows[k]["retries"],
                  rows[k]["tools"], rows[k]["human"], rows[k]["errors"],
                  rows[k]["nothing_shipped"],
                  f"{rows[k]['ms'] / rows[k]['runs']:.0f}"] for k in order]))


def detailed_trace_table(spans):
    """First 60 spans by start time, with their interaction type."""
    children = index_spans(spans)
    rows = [[s.get("operationName", "?")[:40],
             label(derive_interaction(s, children) or ("-", None)),
             f"{s.get('duration', 0) / 1000.0:.2f}"]
            for s in sorted(spans, key=lambda s: s.get("startTime", 0))][:60]
    print(table(["Span", "Interaction", "Duration (ms)"], rows))


def taxonomy_audit(spans):
    """Compare manual `interaction_type` tags (if any) with the derived types.

    Lists any spans where the two disagree.
    """
    children = index_spans(spans)
    declared, derived, disagree = Counter(), Counter(), Counter()
    for s in spans:
        d, g = tag(s, "interaction_type"), derive_interaction(s, children)
        g = label(g) if g else None
        if d:
            declared[d] += 1
        if g:
            derived[g] += 1
        if d and g and d != g:
            disagree[(s.get("_service"), s.get("operationName"), d, g)] += 1
    known = [label(i) for i in TAXONOMY]
    rows = known + sorted((set(declared) | set(derived)) - set(known))
    print(table(["Interaction", "Declared (tags)", "Derived"],
                [[k, declared.get(k, 0), derived.get(k, 0)]
                 for k in dict.fromkeys(rows)]))
    if disagree:
        print("\nSpans where the two disagree:")
        print(table(["Service", "Span", "Declared", "Derived"],
                    [[svc, op, d, g] for (svc, op, d, g) in disagree]))


FEATURES = {"summary_interactions": summary_interactions,
            "per_service_interactions": per_service_interactions,
            "taxonomy_audit": taxonomy_audit,
            "llm_reliability": llm_reliability,
            "human_reviews": human_reviews,
            "pattern_effect": pattern_effect,
            "detailed_trace_table": detailed_trace_table}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--services",
                    default="agent_service,human_service,detection_service",
                    help="comma-separated service names to include")
    ap.add_argument("--jaeger-api", default="http://localhost:16686/api/traces",
                    help="Jaeger API endpoint to fetch traces from")
    ap.add_argument("--feature", default="summary_interactions",
                    choices=sorted(FEATURES))
    ap.add_argument("--patterns", default=None,
                    help="only traces run under this pattern configuration, "
                         "as the `run.patterns` tag spells it — e.g. 'all', "
                         "'none', or 'structured+dispatcher'. Use "
                         "--feature=pattern_effect to list what is available.")
    args = ap.parse_args()

    spans = fetch_spans(args.jaeger_api, args.services.split(","))
    if args.patterns:
        spans = scope_to_patterns(spans, args.patterns)
        if not spans:
            raise SystemExit(
                f"no traces tagged run.patterns={args.patterns!r} — run that "
                f"configuration first, or use --feature=pattern_effect to see "
                f"which configurations are in the window")
    if not spans:
        print("no traces found — run a mission first "
              "(POST http://localhost:8001/mission or use the frontend)")
    else:
        FEATURES[args.feature](spans)
