"""The five patterns, each an on/off flag on a request.

ON runs the disciplined version of the pattern; OFF runs the naive version.
Flags are independent, so all 32 combinations work.

Each registry entry describes:
  tasks       - the tasks whose code this pattern affects; for any other
                task the flag is ignored
  requirement - the problem the pattern solves
  on / off    - what each setting does
  breaks      - what goes wrong when it is off
  observe     - where to see it in Jaeger, Prometheus and the analytics tool

The console shows these entries. The README quotes each `requirement`, so
keep the two in sync.

For `--patterns=<config>` in the analytics commands, pass the run's
`pattern_label` (e.g. "all" or "structured+routing"). Without it, the tool
mixes traces from every configuration.
"""

# ---------------------------------------------------------------------------
# The registry. `key` is the flag name in the request; `number` is the order
# the tutorial introduces the pattern; `tasks` lists the endpoints that use it.
# ---------------------------------------------------------------------------

PATTERNS = [
    {
        "key": 'structured',
        "number": 1,
        "tasks": ('triage', 'investigate', 'mission'),
        "requirement": 'Rescue teams are sent based on victim counts and confidence '
            'values. The model replies with free text that can contain wrong '
            'numbers, so every number must be checked against the drone '
            'detections before it reaches the map.',
        "title": 'Structured outputs: parse → validate → retry',
        "on": 'Find the JSON in the reply, check each value against the detection'
            ' data, and if something is wrong, ask again with the error message'
            ' included (up to 3 attempts).',
        "off": 'Parse the reply once with json.loads and use it as-is. No checks, '
            'no retry.',
        "breaks": "Wrong numbers reach the map. For example, llama3.2 reports A2's "
            'lowest confidence as 0.85 when the data says 0.84, or counts '
            'debris as people. The map looks valid but is wrong.',
        "observe": {
            "jaeger": 'Each retry is an extra llm.complete span with llm.is_retry=true. '
                'Off: exactly one llm.complete per step, never a retry.',
            "prometheus": 'agent_llm_retries_total increases only when this pattern is on.',
            "analytics": '--feature=llm_reliability (retry rate, calls per task)',
        },
    },
    {
        "key": 'dispatcher',
        "number": 2,
        "tasks": ('investigate', 'mission'),
        "requirement": 'The model has never seen this disaster area. Facts must come from '
            'the drone data (detection_service), and the model must be able to '
            'ask for them without getting direct access to the system.',
        "title": 'Tool use through a controlled dispatcher',
        "on": 'The model asks for a tool by name. The agent checks the name '
            'against an allowlist, makes the HTTP call itself, and adds the '
            'result to the prompt as an OBSERVATION line. Errors go back to the'
            ' model as text.',
        "off": 'No tools. The model answers from memory, without any real data.',
        "breaks": 'The answers are made up. The model invents victims, counts and '
            'confidence values that look plausible but come from no real data.',
        "observe": {
            "jaeger": 'tool.get_detections, tool.weather and tool.drone_status spans '
                'appear under the task, with their arguments in tool.args. Off: no '
                'tool spans, and the agent never calls detection_service for data.',
            "prometheus": 'agent_external_requests_total stops increasing.',
            "analytics": '--feature=summary_interactions --patterns=<config> — '
                'S2S:ai_to_service collapses to 1 (9 → 1 on a default mission). The'
                " one survivor is the agent's own /sectors scope fetch, which is "
                'code-driven orchestration, not model-requested tool use; every '
                'per-sector detection read is gone.',
        },
    },
    {
        "key": 'routing',
        "number": 3,
        "tasks": ('triage', 'mission'),
        "requirement": 'Field reports are mixed: medical, structural, logistics, and '
            'noise. Each type needs different handling and noise needs none, so'
            ' the type must be decided before a full LLM call is spent on the '
            'report.',
        "title": 'Workflow: routing',
        "on": 'One short classify call labels the report (medical, structural, '
            'logistics or ignore), then the specialist prompt for that label '
            "handles it. 'ignore' reports stop after the classify call. Runs in"
            " triage and in the mission's field reports.",
        "off": 'One general prompt classifies and handles every report in a single'
            ' call.',
        "breaks": 'Junk reports cost a full generation instead of one word (measured:'
            ' 101 tokens and 725 ms vs 46 tokens and 91 ms), and the general '
            'prompt failed 1 run in 6. Routing is not automatically more '
            'accurate: on llama3.2 the standalone classifier scored 6/10 '
            "against the general prompt's 10/10.",
        "observe": {
            "jaeger": 'The triage span has triage.label and triage.route. On: two '
                'llm.complete children (classify, then specialist), or one for '
                "'ignore'. Off: always one.",
            "prometheus": 'agent_llm_requests_total per report: on = 2 calls (1 for '
                "'ignore'), off = always 1, but a full-length one.",
            "analytics": '--feature=llm_reliability — the LLM Task column splits into triage'
                ' + handler when routing is on.',
        },
    },
    {
        "key": 'parallel',
        "number": 4,
        "tasks": ('mission',),
        "requirement": 'The mission summarizes six sectors, each with its own LLM call. '
            "The calls don't depend on each other, so running them one at a "
            'time takes about six times as long for the same result.',
        "title": 'Workflow: parallelization',
        "on": 'The six sector summaries run at the same time in a thread pool. '
            'Each worker gets the parent trace context, so its spans stay under'
            ' phase.survey.',
        "off": 'The six sector summaries run one after another.',
        "breaks": 'Nothing becomes wrong; the mission just takes longer. This is the '
            'only pattern that improves speed rather than correctness.',
        "observe": {
            "jaeger": 'Open the phase.survey span. On: the six llm.complete spans '
                '(llm.task=summarize_*) overlap. Off: they run one after another. '
                'Compare the duration of phase.survey.',
            "prometheus": 'The number of calls is the same either way; only the timing '
                'changes.',
            "analytics": '--feature=summary_interactions --patterns=<config> — Avg Duration '
                "for S2S:ai_to_llm barely moves; the survey span's wall clock is "
                'what shrinks.',
        },
    },
    {
        "key": 'human_gate',
        "number": 5,
        "tasks": ('mission',),
        "requirement": 'A victim map sends real rescue teams, so a human must approve it '
            "before it is used, and the agent must act on the human's feedback,"
            ' not just record it.',
        "title": 'Agentic loop with a human gate',
        "on": 'Draft the map, run a code check, then send it to the human expert '
            'panel. If rejected, find the sector named in the reason, '
            'investigate it with tools, and resubmit. Up to 4 rounds.',
        "off": 'The first draft is used with no human review, even if the code '
            'check fails.',
        "breaks": 'Sector B1 has one person detection at 0.62 confidence, in smoke. '
            'The panel rejects it until it is verified; without review, it goes'
            ' to rescuers as a normal victim location.',
        "observe": {
            "jaeger": 'A human.review span with vote_by_expert* children; its duration is'
                ' the human decision time. Off: the trace ends at the draft and has'
                ' no human spans.',
            "prometheus": 'human_review_requests_total and human_review_rejections_total stay'
                ' flat.',
            "analytics": '--feature=summary_interactions --patterns=<config> — the H2S row '
                'goes to 0. An empty row is a finding: this is a system with no '
                'human in it.',
        },
    },
]

BY_KEY = {p["key"]: p for p in PATTERNS}
KEYS = tuple(p["key"] for p in PATTERNS)


def used_by(task):
    """Keys of the patterns that `task` actually uses, in registry order."""
    return tuple(p["key"] for p in PATTERNS if task in p["tasks"])

# Default: every pattern on.
DEFAULTS = {k: True for k in KEYS}


class Patterns:
    """Pattern flags for one request.

    Patterns({"human_gate": False}) -> every flag on except human_gate.
    Missing keys default to on; unknown keys raise ValueError.
    Read a flag as an attribute: `flags.structured`.
    """

    def __init__(self, flags=None):
        supplied = flags or {}
        unknown = sorted(set(supplied) - set(KEYS))
        if unknown:
            raise ValueError(f"unknown pattern(s) {unknown}; "
                             f"valid keys: {list(KEYS)}")
        self._flags = {k: bool(supplied.get(k, DEFAULTS[k])) for k in KEYS}

    def __getattr__(self, name):
        try:
            return self._flags[name]
        except KeyError:
            raise AttributeError(name) from None

    def as_dict(self):
        return dict(self._flags)

    def replace(self, **changes):
        """Return a copy with some flags changed (used by /compare)."""
        return Patterns({**self._flags, **changes})

    def label(self):
        """Short name for this config: "all", "none", or the enabled keys
        joined with "+" (e.g. "structured+routing").

        Stored on spans as `run.patterns`; the analytics tool groups by it.
        """
        on = [k for k in KEYS if self._flags[k]]
        if len(on) == len(KEYS):
            return "all"
        if not on:
            return "none"
        return "+".join(on)

    def enabled_count(self):
        """Number of patterns switched on."""
        return sum(self._flags.values())
