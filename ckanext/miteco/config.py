

# Default MITECO DCAT metadata configuration
MITECO_DEFAULT_HVD_CATEGORY = 'http://data.europa.eu/bna/c_dd313021'
MITECO_INSPIRE_GENERAL_TYPE = 'http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL'
MITECO_HVD_GENERAL_TYPE = 'http://publications.europa.eu/resource/authority/dataset-type/HVD'
MITECO_DEFAULT_GENERAL_TYPE_HVDS = [MITECO_INSPIRE_GENERAL_TYPE, MITECO_HVD_GENERAL_TYPE]


# OGC2CKAN Harvester Metadata Configuration
from ckanext.inspire.defaults import OGC2CKAN_HARVESTER_MD_CONFIG

RDF_DEFAULT_MAPPING = {
    'dataset':{'title_translated': 'dct:title', 'identifier': 'dct:identifier', 'name': 'dcat:landingPage', 'dcat_type': 'dct:type', 'theme_es': 'dcat:theme', 'hvd_category': 'dcatap:hvdCategory', 'language': 'dct:language', 'created': 'dct:created', 'modified': 'dct:modified', 'miteco_identifier': 'dct:identifier', 'notes_translated': 'dct:description', 'topic': 'dcat:keyword', 'tag_string': 'dct:subject', 'contact_name': 'dcat:contactPoint', 'contact_email': 'vcard:hasEmail', 'contact_url': 'vcard:hasURL', 'contact_role': 'dcat:hadRole', 'publisher_name': 'foaf:name', 'publisher_identifier': 'dct:identifier', 'publisher_email': 'foaf:mbox', 'publisher_url': 'foaf:homepage', 'publisher_type': 'dct:type', 'maintainer': 'dcat:contactPoint', 'maintainer_email': 'vcard:hasEmail', 'maintainer_url': 'foaf:homepage', 'author': 'dct:creator', 'author_email': 'vcard:hasEmail', 'author_url': 'foaf:homepage', 'author_type': 'dct:type', 'alternate_identifier': 'adms:identifier', 'provenance': 'dct:provenance', 'conforms_to': 'dct:conformsTo', 'metadata_profile': 'dct:conformsTo', 'applicable_legislation': 'dcatap:applicableLegislation', 'temporal_start': 'dct:temporal', 'temporal_end': 'dct:temporal', 'frequency': 'dct:accrualPeriodicity', 'source': 'dct:source', 'lineage_source': 'dct:source', 'reference': 'dcat:relation', 'is_referenced_by': 'dct:isReferencedBy', 'encoding': 'cnt:characterEncoding', 'theme': 'dcat:theme', 'inspire_id': 'adms:identifier', 'spatial_uri': 'dct:spatial', 'representation_type': 'adms:representationTechnique', 'spatial_resolution_in_meters': 'dcat:spatialResolutionInMeters', 'license_id': 'dct:license', 'access_rights': 'dct:accessRights', 'version': 'owl:versionInfo', 'has_version': 'dcat:hasVersion', 'version_notes': 'adms:versionNotes', 'valid': 'dct:valid'},
    'resource':{'access_url': 'dcat:accessURL', 'download_url': 'dcat:downloadURL', 'access_services': 'dcat:downloadURL', 'description': 'dct:description', 'created': 'dct:created', 'modified': 'dct:modified', 'hash': 'spdx:checksumValue', 'hash_algorithm': 'spdx:Checksum', 'availability': 'dcatap:availability', 'spatial_resolution_in_meters': 'dcat:spatialResolutionInMeters', 'format': 'dct:format', 'mimetype': 'dct:MediaType', 'compress_format': 'dcat:compressFormat', 'package_format': 'dcat:packageFormat', 'status': 'adms:status', 'encoding': 'cnt:characterEncoding', 'size': 'dcat:byteSize', 'language': 'dct:language', 'license': 'dct:license', 'rights': 'dct:accessRights', 'conforms_to': 'dct:conformsTo', 'applicable_legislation': 'dcatap:applicableLegislation', 'name': 'dct:title'}
}

RDF_PREFIX = f"""
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX hydra: <http://www.w3.org/ns/hydra/core#>
PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
PREFIX spdx: <http://spdx.org/rdf/terms#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX locn: <http://www.w3.org/ns/locn#>
PREFIX cnt: <http://www.w3.org/2011/content#>
PREFIX dcatap: <http://data.europa.eu/r5r/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX eli: <http://data.europa.eu/eli/ontology#>
"""

from ckanext.inspire.defaults import RDF_DATASET_TEMPLATE

RDF_RESOURCE_TEMPLATE =      {
        "applicable_legislation": [],
        "availability": "",
        "cache_last_updated": None,
        "cache_url": None,
        "compress_format": "",
        "conforms_to": [],
        "created": "2026-02-04T00:00:00",
        "datastore_active": False,
        "datastore_contains_all_records_of_source_file": False,
        "description": "",
        "documentation": [],
        "encoding": "",
        "format": "",
        "hash": "",
        "hash_algorithm": "",
        "language": "",
        "last_modified": None,
        "license": "",
        "metadata_modified": "2026-02-04T16:49:51.090895",
        "mimetype": "",
        "mimetype_inner": None,
        "modified": "2026-02-04",
        "name": "plantilla",
        "package_format": "",
        "position": 0,
        "reference_system": "",
        "resource_relation": [],
        "resource_type": None,
        "rights": "",
        "size": 0,
        "spatial_resolution_in_meters": "",
        "state": "active",
        "status": "",
        "temporal_resolution": "",
        "url": "https://www.example.com",
        "url_type": "",
        "access_services": [
          {
            "endpoint_description": "",
            "endpoint_url": [],
            "serves_dataset": [],
            "title": "",
            "uri": ""
          }
        ]
      }

miteco_rdf_parser = None
