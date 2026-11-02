# Semantica Northstar Authorization POC

A compact proof of concept for time-aware document authorization using Semantica. It demonstrates a Northstar-specific mapping adapter, KG construction, temporal queries, recursive team/project reachability, policy evaluation, and explanation hooks.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m northstar_authz --person Alice --as-of 2026-11-01T12:00:00Z
```

See [architecture](docs/architecture.md), [sequence](docs/sequence.md), and [activity](docs/activity.md).

This is a demonstration, not a production authorization system. See the module boundaries and modelling caveats in the diagrams and code.
