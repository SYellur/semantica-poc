"""Small semantic diff for Northstar Turtle ontology files."""
from __future__ import annotations

from pathlib import Path
from rdflib import Graph, Namespace, OWL, RDF, RDFS

NS = Namespace("https://example.org/northstar#")


def _signature(path: str | Path) -> dict[str, set[tuple[str, str, str]]]:
    graph = Graph()
    graph.parse(str(path), format="turtle")
    result: dict[str, set[tuple[str, str, str]]] = {
        "classes": set(), "object_properties": set(), "datatype_properties": set(),
        "domains": set(), "ranges": set(),
    }
    for subject in graph.subjects(RDF.type, OWL.Class):
        result["classes"].add((str(subject), "", ""))
    for kind, label in ((OWL.ObjectProperty, "object_properties"),
                        (OWL.DatatypeProperty, "datatype_properties")):
        for subject in graph.subjects(RDF.type, kind):
            result[label].add((str(subject), "", ""))
    for subject, value in graph.subject_objects(RDFS.domain):
        result["domains"].add((str(subject), str(value), ""))
    for subject, value in graph.subject_objects(RDFS.range):
        result["ranges"].add((str(subject), str(value), ""))
    return result


def diff_ontologies(old_path: str | Path, new_path: str | Path) -> dict[str, dict[str, list[str]]]:
    """Report additions/removals of classes, properties, domains, and ranges."""
    old, new = _signature(old_path), _signature(new_path)
    diff = {}
    for category in old:
        added = sorted(new[category] - old[category])
        removed = sorted(old[category] - new[category])
        diff[category] = {
            "added": [" ".join(item).strip() for item in added],
            "removed": [" ".join(item).strip() for item in removed],
        }
    return diff
