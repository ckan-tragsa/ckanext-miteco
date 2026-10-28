"""Corrections of existing INSPIRE fields after the standard RDF readers."""
import json
from rdflib import Namespace, URIRef, RDF, BNode, Literal

DCT = Namespace('http://purl.org/dc/terms/')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
GEO = Namespace('http://data.europa.eu/930/')
PROV = Namespace('http://www.w3.org/ns/prov#')
SCHEMA = Namespace('http://schema.org/')
DATE_FIELDS = (('created', DCT.created), ('modified', DCT.modified),
               ('miteco_publication_date', DCT.issued))


def read_fields(profile, data, subject):
    graph = profile.g
    for field, predicate in DATE_FIELDS:
        value = graph.value(subject, predicate)
        data[field] = str(value) if value is not None else ''
    for field, predicate in (('reference_system', GEO.referenceSystem),
                             ('frequency', DCT.accrualPeriodicity),
                             ('representation_type', Namespace('http://www.w3.org/ns/adms#').representationTechnique),
                             ('access_rights', DCT.accessRights)):
        value = graph.value(subject, predicate)
        if isinstance(value, URIRef):
            data[field] = str(value)
    spatial = profile._spatial(subject, DCT.spatial)
    if spatial.get('geom'):
        geometry = spatial['geom']
        data['spatial'] = geometry if isinstance(geometry, str) else json.dumps(geometry)
    statements = [text for node in graph.objects(subject, DCT.provenance)
                  for text in graph.objects(node, DCT.description)]
    if statements:
        data['provenance'] = {}
        for text in statements:
            lang = text.language or profile._default_lang
            previous = data['provenance'].get(lang)
            data['provenance'][lang] = previous + '\n' + str(text) if previous else str(text)
    for field, predicate in (('lineage_source', DCT.source), ('lineage_process_steps', PROV.wasGeneratedBy)):
        nodes = [node for node in graph.objects(subject, predicate) if graph.value(node, DCT.description)]
        nodes.sort(key=lambda node: int(graph.value(node, SCHEMA.position) or 0))
        if nodes:
            data[field] = [str(graph.value(node, DCT.description)) for node in nodes]
    # dct:source also populates the legacy 'source' field in the base reader.
    # That name is reserved as a scalar by CKAN's Solr schema. Keep lineage
    # descriptions/URIs in the existing lineage_source field instead.
    sources = list(graph.objects(subject, DCT.source))
    if sources:
        data.pop('source', None)
        data['extras'] = [extra for extra in data.get('extras', [])
                          if extra.get('key') != 'source']
        described = data.get('lineage_source') or []
        direct = [str(node) for node in sources if isinstance(node, (URIRef, Literal))]
        data['lineage_source'] = list(dict.fromkeys(described + direct))
        dataset_sources = [str(node) for node in sources if isinstance(node, URIRef)]
        if len(dataset_sources) == 1:
            data['source'] = dataset_sources[0]
    keywords = [str(text) for text in graph.objects(subject, DCAT.keyword)]
    if keywords:
        data['tag_string'] = ','.join(text.replace(',', ' ') for text in keywords)
    references = list(graph.objects(subject, DCAT.servesDataset))
    if references:
        data['reference'] = list(dict.fromkeys((data.get('reference') or []) + [str(v) for v in references]))
    if not data.get('resources'):
        endpoints = list(dict.fromkeys(graph.objects(subject, DCAT.endpointURL)))
        data['resources'] = [{'url': str(url), 'access_url': str(url),
                              'name': str(graph.value(subject, DCT.title) or url)} for url in endpoints]
    return data


def write_fields(profile, data, subject):
    graph = profile.g
    # ADMS identifiers are resources; textual codes belong in skos:notation.
    # Keep the code (and its datatype/language) rather than inventing a URI.
    adms = Namespace('http://www.w3.org/ns/adms#')
    skos = Namespace('http://www.w3.org/2004/02/skos/core#')
    for value in list(graph.objects(subject, adms.identifier)):
        if isinstance(value, Literal):
            node = BNode()
            graph.remove((subject, adms.identifier, value))
            graph.add((subject, adms.identifier, node))
            graph.add((node, RDF.type, adms.Identifier))
            graph.add((node, skos.notation, value))
    for field, predicate in DATE_FIELDS:
        graph.remove((subject, predicate, None))
        if data.get(field):
            profile._add_date_triple(subject, predicate, data[field])
    for field, predicate in (('lineage_source', DCT.source), ('lineage_process_steps', PROV.wasGeneratedBy)):
        if data.get(field):
            graph.remove((subject, predicate, None))
            source = data.get('source') if field == 'lineage_source' else None
            if source:
                graph.add((subject, predicate, URIRef(source)))
            for position, text in enumerate(data[field], 1):
                if text == source:
                    continue
                node = BNode()
                graph.add((subject, predicate, node))
                graph.add((node, DCT.description, Literal(text)))
                graph.add((node, SCHEMA.position, Literal(position)))
    if data.get('reference_system'):
        graph.set((subject, GEO.referenceSystem, URIRef(data['reference_system'])))
    if str(data.get('dcat_type', '')).endswith('/service'):
        graph.remove((subject, RDF.type, DCAT.Dataset))
        graph.add((subject, RDF.type, DCAT.DataService))
        for resource in data.get('resources', []):
            if resource.get('access_url') or resource.get('url'):
                graph.add((subject, DCAT.endpointURL, URIRef(resource.get('access_url') or resource['url'])))
