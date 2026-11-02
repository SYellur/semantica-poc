from northstar_authz.ontology_generation import build_generation_prompt
from northstar_authz.service import load_data


def test_generation_prompt_preserves_temporal_association_requirements():
    prompt = build_generation_prompt(load_data())
    assert "DirectDocumentShare" in prompt
    assert "DocumentRestriction" in prompt
    assert "validFrom and validUntil as xsd:dateTime" in prompt
    assert "effectiveFrom as xsd:dateTime" in prompt
    assert "source-to-ontology mapping" in prompt
