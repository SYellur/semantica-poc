from northstar_authz.ontology_validation import validate_ontology_mapping
from northstar_authz.service import load_data


def test_current_ontology_and_adapter_mapping_validate():
    assert validate_ontology_mapping(load_data()) == []


def test_validator_detects_silently_dropped_source_relationship():
    data = load_data()
    data["direct_shares"] = data["direct_shares"][:-1]
    errors = validate_ontology_mapping(data)
    assert any("Mapping coverage for directShareTo" in error for error in errors)


def test_validator_detects_undeclared_or_mistyped_projection_property(tmp_path):
    data = load_data()
    ontology = tmp_path / "changed.ttl"
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "ontology" / "northstar.ttl"
    ).read_text()
    ontology.write_text(source.replace(
        "ns:directShareTo a owl:ObjectProperty ;",
        "ns:directShareTo a owl:DatatypeProperty ;",
    ))
    errors = validate_ontology_mapping(data, ontology)
    assert any("not a declared owl:ObjectProperty" in error for error in errors)
