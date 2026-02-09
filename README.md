# Hub vs Spoke — LLM Topology Test Harness

When you wire multiple LLM agents together, the coordination pattern matters. This
harness runs the same set of tasks through two topologies — hub-and-spoke and
spoke-and-spoke — then measures how each performs on output quality, token cost, and
fault tolerance.

The point is to answer a practical question: **does a central orchestrator produce
better results than a flat peer mesh, and at what cost?**

## The two topologies

### Hub-and-spoke

One strong model acts as the orchestrator. It receives the task, breaks it into
subtasks, farms each out to cheaper "spoke" models, collects the results, and
synthesises a final answer. All communication flows through the hub.

```
              ┌────────┐
         ┌───►│Spoke A │───┐
         │    └────────┘   │
┌─────┐  │   ┌────────┐   │  ┌─────┐
│User │──┼──►│  Hub   │◄──┼──│Final│
└─────┘  │   └────────┘   │  └─────┘
         │    ┌────────┐   │
         └───►│Spoke B │───┘
              └────────┘
```

Step by step:

1. **Decompose** — Hub receives the task and returns a JSON array of subtask strings.
2. **Delegate** — Each subtask is assigned to a spoke (round-robin). Failed spokes are
   retried up to `max_retries` times before recording a failure.
3. **Synthesise** — Hub receives all spoke outputs and produces a single coherent answer.

The tradeoff: the hub is a single point of failure, but it keeps coherence high because
one model sees the full picture.

### Spoke-and-spoke (peer mesh)

No permanent orchestrator. A group of peer-tier models self-organise: the first peer
decomposes the task, all peers execute subtasks, a middle peer reviews outputs for
consistency, and the last peer synthesises.

```
    ┌─────────┐     ┌─────────┐
    │ Peer 0  │◄───►│ Peer 1  │
    │(coord)  │     │(review) │
    └────┬────┘     └────┬────┘
         │               │
         └──────┬────────┘
                │
          ┌─────┴─────┐
          │  Peer 2   │
          │(synthesise)│
          └───────────┘
```

Step by step:

1. **Decompose** — Peer 0 (coordinator) breaks the task into N subtasks, one per peer.
2. **Execute** — Each peer works on its subtask. Failures are retried, then recorded.
3. **Review** — The middle peer cross-checks all outputs and flags inconsistencies.
4. **Synthesise** — The last peer merges outputs into a final answer.

The tradeoff: no single point of failure (the coordinator role is lightweight and can
in principle be reassigned), but coherence depends on the review and synthesis steps
doing their jobs well.

## What gets measured

Every topology run records:

| Metric | How it's captured |
|---|---|
| **Token usage** | Input + output tokens per turn, summed per run |
| **Cost (USD)** | Tokens mapped to per-model pricing tables (OpenAI and Anthropic rates) |
| **Wall time** | End-to-end milliseconds for the full run |
| **Turn count** | Number of agent-to-agent exchanges |
| **Error count** | Exceptions caught during spoke/peer execution |
| **Final answer** | The synthesised output text |

Evaluation happens through four methods, chosen per task:

- **Exact match** — normalised substring check against a known answer
- **Regex match** — pattern match for structured answers
- **Code execution** — run generated code in a subprocess, check exit code
- **LLM-as-judge** — a separate model scores output quality (1–10 absolute, or
  pairwise A-vs-B comparison)

## Benchmark task categories

There are 17 tasks across five categories:

| Category | # Tasks | Examples |
|---|---|---|
| **Coding** | 4 | Merge sorted lists, debug off-by-one, refactor opaque function, implement LRU cache |
| **Reasoning** | 4 | Fencing optimisation, missing-dollar puzzle, 12-ball weighing, constraint seating |
| **Research** | 3 | DB connection pooling comparison, distributed topology tradeoffs, LLM alignment methods |
| **Creative** | 3 | Short story (AI consciousness), technical blog intro, architecture debate dialogue |
| **Tool use** | 3 | Multi-tool orchestration, sequential data-dependent calls, caching strategy |

Each task specifies its evaluation method. Coding tasks use code execution where
possible; reasoning uses exact match or LLM judge; creative and research use LLM judge;
tool-use checks that the right function calls appear in the right order.

## Default benchmark configurations

The benchmark runner tests five configurations out of the box:

| Label | Topology | Hub model | Spoke/peer models |
|---|---|---|---|
| `claude-hub+gpt-spokes` | Hub-spoke | Claude Sonnet 4 | 3 × GPT-4o-mini |
| `gpt-hub+claude-spokes` | Hub-spoke | GPT-4o | 3 × Claude 3.5 Haiku |
| `gpt-peers` | Spoke-spoke | — | 3 × GPT-4o |
| `claude-peers` | Spoke-spoke | — | 3 × Claude Sonnet 4 |
| `mixed-peers` | Spoke-spoke | — | GPT-4o + Claude Sonnet 4 + GPT-4o-mini |

This gives you cross-provider comparisons (OpenAI hub with Anthropic workers and vice
versa), same-provider peer meshes, and a mixed-provider mesh.

## Setup

**Prerequisites:** Python 3.11+, [`uv`](https://docs.astral.sh/uv/) (recommended) or pip.

```bash
# Clone and install
git clone https://github.com/strangeloopcanon/hub-vs-spoke.git
cd hub-vs-spoke
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Set up API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and ANTHROPIC_API_KEY
```

The OpenAI and Anthropic SDKs read their API keys directly from `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY` environment variables. The `.env` file is loaded automatically.

## Running the tests

```bash
# Unit tests — no API keys, no network, runs in < 1 second
pytest -m "not live" -v

# Unit tests with coverage report
pytest -m "not live" --cov=hub_vs_spoke --cov-report=term-missing

# Live integration tests — requires API keys, makes real API calls
pytest -m live -v
```

Unit tests use `MockAgent` (canned responses, no network) and cover the full topology
pipeline, budget enforcement, error injection / fault tolerance, evaluation logic, and
task registry. Live tests run a simple multiplication task through both topologies with
real models and assert the correct answer appears.

## Running the benchmark

```bash
# Full matrix: 5 configs × 17 tasks × 1 rep = 85 runs
python scripts/run_benchmark.py

# Preview what would run without calling any APIs
python scripts/run_benchmark.py --dry-run

# Single category
python scripts/run_benchmark.py --category coding

# Single config
python scripts/run_benchmark.py --config gpt-peers

# More repetitions for statistical robustness
python scripts/run_benchmark.py --reps 5

# Adjust budget per run
python scripts/run_benchmark.py --budget-tokens 30000 --budget-turns 20

# Custom output path
python scripts/run_benchmark.py --output results/run1.jsonl
```

Results are written as one JSON object per line to `benchmark_results.jsonl` (or your
`--output` path). Each line contains:

```json
{
  "config_label": "claude-hub+gpt-spokes",
  "topology_type": "hub-spoke",
  "hub_model": "claude-sonnet-4-20250514",
  "spoke_models": ["gpt-4o-mini", "gpt-4o-mini", "gpt-4o-mini"],
  "category": "coding",
  "task_id": "coding-001",
  "repetition": 0,
  "success": true,
  "total_tokens": 3847,
  "total_cost_usd": 0.0,
  "wall_time_ms": 4210.3,
  "num_turns": 5,
  "num_errors": 0,
  "errors": [],
  "answer_length": 512
}
```

A summary table is printed to stdout after the run completes.

## Project structure

```
src/hub_vs_spoke/
├── types.py               Core data models (Message, Usage, Turn, TopologyResult, etc.)
├── config.py              Settings via pydantic-settings (.env + env vars)
├── providers/
│   ├── base.py            LLMProvider protocol (interface)
│   ├── openai_provider.py OpenAI chat completions wrapper
│   └── anthropic_provider.py  Anthropic messages wrapper
├── agents/
│   ├── agent.py           Agent: wraps a provider with history + cost tracking
│   └── mock_agent.py      MockAgent: deterministic stub for tests
├── topologies/
│   ├── base.py            Topology protocol (interface)
│   ├── _shared.py         Shared logic: subtask parsing, retry, result building
│   ├── hub_spoke.py       Hub-and-spoke implementation
│   └── spoke_spoke.py     Spoke-and-spoke implementation
├── tasks/
│   ├── base.py            Task model, TaskRegistry, evaluation method enum
│   ├── coding.py          4 coding benchmark tasks
│   ├── reasoning.py       4 reasoning benchmark tasks
│   ├── research.py        3 research benchmark tasks
│   ├── creative.py        3 creative benchmark tasks
│   └── tool_use.py        3 tool-use benchmark tasks
└── evaluation/
    ├── judge.py           LLM-as-judge (absolute score + pairwise comparison)
    ├── deterministic.py   Exact match, regex, code execution, function-call check
    ├── cost.py            Token-to-USD cost calculation
    └── reliability.py     Success rate, error rate, topology comparison

tests/
├── conftest.py            Shared fixtures (mock agents, sample tasks, budgets)
├── unit/                  Fast tests, no network
│   ├── test_agent.py
│   ├── test_hub_spoke_topology.py
│   ├── test_spoke_spoke_topology.py
│   ├── test_evaluation.py
│   └── test_tasks.py
└── integration/           Topology pipeline tests (mock + live)
    ├── conftest.py
    ├── test_budget_fairness.py
    ├── test_error_injection.py
    └── test_hub_vs_spoke_comparison.py

scripts/
└── run_benchmark.py       CLI benchmark runner
```

## Adding new tasks

Create a task in the relevant category file (e.g. `src/hub_vs_spoke/tasks/coding.py`):

```python
Task(
    task_id="coding-005",
    category=TaskCategory.CODING,
    prompt="Your task description here.",
    expected_answer="known answer if applicable",     # or None
    eval_method=EvalMethod.CODE_EXECUTION,            # or EXACT_MATCH, LLM_JUDGE, etc.
    eval_rubric="What counts as a good answer.",
    difficulty="medium",
)
```

Append it to the category's task list and it will automatically register with the
default registry on import.

## Adding a new provider

Implement the `LLMProvider` protocol (see `providers/base.py`): a `model_name` property
and an async `complete()` method that takes a list of `Message` objects and returns an
`LLMResponse`. Then wire it into the benchmark script's `_make_provider()` function.

## Budget enforcement

Both topologies check a `TokenBudget(max_total_tokens, max_turns)` between steps. When
the budget is exceeded, the topology stops early and returns whatever partial results it
has. This keeps live benchmark runs from spiralling in cost. The check happens between
steps, not mid-step, so a run may slightly overshoot by one step's worth of tokens.

## Fault tolerance testing

The test suite includes a `FaultyAgent` that fails a configurable percentage of calls.
Tests verify that:

- Hub-spoke recovers from spoke failures (retries, then records error and continues)
- Hub-spoke treats hub failure as unrecoverable (the orchestrator is the single point of failure)
- Spoke-spoke tolerates individual peer failures
- Both topologies still produce a final answer even with partial failures
- Error counts and messages are accurately recorded

A comparative test runs both topologies five times with 30% failure rates and compares
their reliability scores.
