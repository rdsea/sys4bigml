#!/usr/bin/env python3
"""Analyze HIS-LLM interaction metrics from Jaeger tracing data.

Fetches traces from the Jaeger API, walks their spans, and aggregates the
interaction taxonomy (S2S with its sub-kinds, H2S, H2H) plus LLM-specific
signals (retry rate, per-task volume) and human-gate behavior (decision
latency, rejection rate).

The taxonomy is *derived* from the traces here, not tagged at the call sites —
see ``derive_interaction`` for how, and why that is the cheaper half of the
bargain.

Examples:

    python3 mission_analytics.py --feature=summary_interactions
    python3 mission_analytics.py --feature=llm_reliability
    python3 mission_analytics.py --services=agent_service,human_service \
        --jaeger-api=http://localhost:16686/api/traces --feature=human_reviews
"""
import argparse
from collections import Counter, defaultdict

import requests


def fetch_spans(jaeger_api, services, limit=200):
    """All spans of the last `limit` traces of each service, flattened.

    Two details the Jaeger API forces on every consumer:

    - A trace is returned in full by *each* service it touches, so the spans
      of a cross-service trace (every mission) arrive once per service.
      Without the (traceID, spanID) dedupe below, one mission's model calls are
      counted twice or three times — the metrics inflate silently.
    - ``span["processID"]`` is only meaningful *within* its trace; the service
      name lives in the trace's ``processes`` map. Resolve it here, once, into
      ``_service`` so the features downstream can group by service.
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


def tag(span, key, default=None):
    for t in span.get("tags", []):
        if t["key"] == key:
            return t["value"]
    return default


# ---------------------------------------------------------------------------
# Deriving the taxonomy instead of declaring it.
#
# `interaction_type` used to be set by hand at every call site, which made the
# taxonomy a convention N producers had to keep in sync — and a rename nothing
# would catch. None of it was necessary, because a span already says what kind
# of interaction it is. Two tiers, in order of how much they cost you:
#
#   1. TOPOLOGY (free). An interaction across a process boundary is defined by
#      who emitted the span and who they talked to, and auto-instrumentation
#      records both: RequestsInstrumentor emits a client span carrying
#      `http.url` for every hop, and context propagation links it to the
#      callee's server span. One table of roles replaces every hand-set tag.
#
#   2. SPAN NAMES (already paid for). An interaction *inside* one process
#      crosses no boundary, so topology is blind to it. But `llm.complete` and
#      `vote_by_*` are names the instrumentation must choose anyway, and that
#      `llm_reliability` and `human_reviews` below already depend on. Reusing
#      them costs no new convention; a parallel tag would have been a second
#      one to keep in sync.
#
# Tier 2 is a naming convention, not an observation — worth knowing when you
# extend this. What it is *not* is an extra one.
# ---------------------------------------------------------------------------

# The roles a span's service plays in the taxonomy.
ROLES = {"agent_service": "AI",       # an LLM-driven component
         "detection_service": "S",    # a plain software service
         "human_service": "H"}        # humans (the expert panel)

# Peers that run no OTel SDK of their own, so they never emit a span: they are
# recognised from the URL the caller used.
PEER_ROLES = {"11434": "L",           # Ollama's port
              "/api/generate": "L",   # ...or its route, whichever matches
              "/v1/chat/completions": "L"}

# Tier 2: the in-process interactions, keyed on the span names the rest of this
# file already treats as load-bearing.
LLM_SPAN = "llm.complete"             # one model call
VOTE_PREFIX = "vote_by_"              # one expert deliberating

# The taxonomy, declared in full so the report can show a category that this
# system never exercises. An empty row is a finding, not a gap: `orchestration`
# and `H2H` below are both structurally 0 here, and the README explains why.
TAXONOMY = [("S2S", "ai_to_ai"),
            ("S2S", "ai_to_service"),
            ("S2S", "orchestration"),
            ("H2S", None),
            ("H2H", None)]


def label(interaction):
    """("S2S", "ai_to_ai") -> "S2S:ai_to_ai"; ("H2S", None) -> "H2S"."""
    category, subkind = interaction
    return f"{category}:{subkind}" if subkind else category


def index_spans(spans):
    """Child spans indexed by their parent's (traceID, spanID)."""
    children = defaultdict(list)
    for span in spans:
        for ref in span.get("references", []):
            if ref.get("refType") == "CHILD_OF":
                children[(ref.get("traceID"), ref.get("spanID"))].append(span)
    return children


def peer_role(span, children):
    """Who is on the other end of this client span?"""
    # Preferred: the callee instrumented itself, so its server span is our
    # child and names its own service.
    for child in children.get((span.get("traceID"), span.get("spanID")), []):
        if child.get("_service") != span.get("_service"):
            return ROLES.get(child.get("_service"))
    # Fallback: an uninstrumented peer (Ollama) — read it off the URL.
    url = tag(span, "http.url", "") or ""
    for marker, role in PEER_ROLES.items():
        if marker in url:
            return role
    return None


def derive_interaction(span, children):
    """The (category, sub-kind) a span implies, or None if it implies none.

    S2S covers everything between computational components — the agent, the
    model and the services — split by sub-kind because the *failure and cost
    models* differ: an `ai_to_ai` call fails as HTTP 200 carrying unusable
    content, an `ai_to_service` call fails as a 404 or a timeout. H2S is any
    interaction that crosses to or from a human. H2H would be humans
    interacting through a service, which this system does not do.
    """
    source = ROLES.get(span.get("_service"))
    if source is None:
        return None
    op = span.get("operationName", "")
    # -- tier 2: in-process, recognised by name --
    if op == LLM_SPAN and source == "AI":
        # Counted here rather than on the HTTP hop underneath, so the label
        # survives swapping a remote model for an in-process one: such a
        # backend emits no client span at all, and this still reports S2S.
        return ("S2S", "ai_to_ai")
    if op.startswith(VOTE_PREFIX) and source == "H":
        # An expert's decision, recorded by the service: human -> service.
        return ("H2S", None)
    # -- tier 1: across a boundary, read off the topology --
    if tag(span, "span.kind") == "client":
        target = peer_role(span, children)
        if target is None or target == "L":
            # The POST to Ollama is already counted on its llm.complete parent.
            return None
        # Counted on the client side only: one edge, one interaction. The
        # callee's server span is the same interaction seen from the far end,
        # which is why tagging both ends used to double-count the human gate.
        if target == "H" or source == "H":
            return ("H2S", None)
        if target == "AI":
            return ("S2S", "ai_to_ai")
        # An LLM-agent reaching a supporting module, versus plain
        # workflow-driven traffic between two services.
        return ("S2S", "ai_to_service" if source == "AI" else "orchestration")
    return None


def table(headers, rows):
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


def detailed_trace_table(spans):
    children = index_spans(spans)
    rows = [[s.get("operationName", "?")[:40],
             label(derive_interaction(s, children) or ("-", None)),
             f"{s.get('duration', 0) / 1000.0:.2f}"]
            for s in sorted(spans, key=lambda s: s.get("startTime", 0))][:60]
    print(table(["Span", "Interaction", "Duration (ms)"], rows))


def taxonomy_audit(spans):
    """Hand-set `interaction_type` tags vs the labels derived here.

    Run this *before* deleting tags from a service: it proves the derivation
    reproduces them. Afterwards the declared column reads 0, which is the
    confirmation the tags are gone and nothing regressed.
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
    args = ap.parse_args()

    spans = fetch_spans(args.jaeger_api, args.services.split(","))
    if not spans:
        print("no traces found — run a mission first "
              "(POST http://localhost:8001/mission or use the frontend)")
    else:
        FEATURES[args.feature](spans)
