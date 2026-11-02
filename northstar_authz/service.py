"""Load sample data and expose Semantica KG/temporal entry points."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .adapter import source_to_kg


def load_data(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "data" / "northstar.json"
    with source.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_graph(data: dict[str, Any]) -> dict[str, Any]:
    from semantica.kg import GraphBuilder
    return GraphBuilder().build(source_to_kg(data))


def temporal_snapshot(graph: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    from semantica.kg import TemporalGraphQuery
    return TemporalGraphQuery().query_at_time(graph, query="", at_time=as_of)
