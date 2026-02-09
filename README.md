# Hub vs Spoke LLM Topology Test Harness

Lightweight Python test harness that systematically compares **hub-and-spoke** vs
**spoke-and-spoke** (peer mesh) LLM agent topologies across quality, cost, and
reliability metrics.

## Quick start

```bash
# Create a virtual environment and install
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Copy and fill in your API keys
cp .env.example .env

# Run unit tests (no API keys needed)
pytest -m "not live" -v

# Run live integration tests (requires API keys)
pytest -m live -v

# Run the full benchmark matrix
python scripts/run_benchmark.py
```

## Topologies

| Topology | Description |
|---|---|
| Hub-and-spoke | Central orchestrator (strong model) decomposes, delegates to cheaper spokes, synthesises |
| Spoke-and-spoke | Peer mesh of medium-tier models that coordinate directly without a single orchestrator |

## Metrics captured

- **Quality** -- LLM-as-judge (pairwise) and deterministic checks where applicable
- **Cost** -- per-run token usage mapped to provider pricing
- **Reliability** -- success rate, error recovery, graceful degradation under fault injection
