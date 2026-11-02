from pathlib import Path

from northstar_authz.ontology_diff import diff_ontologies


def test_ontology_diff_reports_added_and_removed_classes(tmp_path):
    root = Path(__file__).resolve().parents[1]
    old = root / "ontology" / "northstar.ttl"
    changed = tmp_path / "changed.ttl"
    changed.write_text(old.read_text().replace("ns:Person a owl:Class .", "ns:Human a owl:Class ."))
    report = diff_ontologies(old, changed)
    assert any("northstar#Human" in item for item in report["classes"]["added"])
    assert any("northstar#Person" in item for item in report["classes"]["removed"])
