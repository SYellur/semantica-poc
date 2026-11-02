from pathlib import Path

from rdflib import Graph, Namespace, OWL, RDF, RDFS, URIRef


def test_northstar_ontology_parses_and_defines_temporal_association_properties():
    ontology_path = Path(__file__).resolve().parents[1] / "ontology" / "northstar.ttl"
    graph = Graph()
    graph.parse(ontology_path, format="turtle")

    ns = Namespace("https://example.org/northstar#")
    assert (ns.DirectDocumentShare, RDF.type, OWL.Class) in graph
    assert (ns.DocumentRestriction, RDF.type, OWL.Class) in graph
    assert (ns.validFrom, RDF.type, OWL.DatatypeProperty) in graph
    assert (ns.validUntil, RDFS.range, URIRef('http://www.w3.org/2001/XMLSchema#dateTime')) in graph
    assert (ns.effectiveFrom, RDFS.range, URIRef('http://www.w3.org/2001/XMLSchema#dateTime')) in graph
