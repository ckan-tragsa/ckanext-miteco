"""ADMS literal codes keep their value in the existing MITECO RDF profile."""
from types import SimpleNamespace
from rdflib import Graph, Namespace, URIRef, Literal, RDF, BNode
from ckanext.miteco.inspire.fields import write_fields


def test_literal_identifiers_are_resources_without_losing_codes():
    graph = Graph()
    subject = URIRef('urn:test:dataset')
    adms = Namespace('http://www.w3.org/ns/adms#')
    skos = Namespace('http://www.w3.org/2004/02/skos/core#')
    codes = [Literal('España-123', lang='es'), Literal('456')]
    uri = URIRef('https://example.invalid/identifier')
    for value in codes + [uri]:
        graph.add((subject, adms.identifier, value))
    profile = SimpleNamespace(g=graph)
    write_fields(profile, {}, subject)
    assert (subject, adms.identifier, uri) in graph
    nodes = [n for n in graph.objects(subject, adms.identifier) if isinstance(n, BNode)]
    assert len(nodes) == 2
    assert set(graph.objects(None, skos.notation)) == set(codes)
    assert all((n, RDF.type, adms.Identifier) in graph for n in nodes)
    size = len(graph)
    write_fields(profile, {}, subject)
    assert len(graph) == size
