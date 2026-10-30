

# Default MITECO DCAT metadata configuration
MITECO_DEFAULT_HVD_CATEGORY = 'http://data.europa.eu/bna/c_dd313021'
MITECO_INSPIRE_GENERAL_TYPE = 'http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL'
MITECO_HVD_GENERAL_TYPE = 'http://publications.europa.eu/resource/authority/dataset-type/HVD'
MITECO_DEFAULT_GENERAL_TYPE_HVDS = [MITECO_INSPIRE_GENERAL_TYPE, MITECO_HVD_GENERAL_TYPE]


# OGC2CKAN Harvester Metadata Configuration
OGC2CKAN_HARVESTER_MD_CONFIG = {
    'access_rights': 'http://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess/noLimitations',
    'conformance': [
        'http://inspire.ec.europa.eu/documents/inspire-metadata-regulation','http://inspire.ec.europa.eu/documents/commission-regulation-eu-no-13122014-10-december-2014-amending-regulation-eu-no-10892010-0'
    ],
    'author_name': 'Ministerio para la Transición Ecológica y el Reto Demográfico',
    'author_email': 'bzn-sig-miteco@miteco.es',
    'author_url': 'https://www.miteco.gob.es/',
    'author_uri': 'http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001',
    'contact_name': 'Ministerio para la Transición Ecológica y el Reto Demográfico',
    'contact_email': 'bzn-sig-miteco@miteco.es',
    'contact_url': 'https://www.miteco.gob.es/',
    'contact_uri': 'http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001',
    'dcat_type': {
        'series': 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/series',
        'dataset': 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/dataset',
        'spatial_data_service': 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/service',
        'default': 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/dataset',
        'collection': 'http://purl.org/dc/dcmitype/Collection',
        'event': 'http://purl.org/dc/dcmitype/Event',
        'image': 'http://purl.org/dc/dcmitype/Image',
        'still_image': 'http://purl.org/dc/dcmitype/StillImage',
        'moving_image': 'http://purl.org/dc/dcmitype/MovingImage',
        'physical_object': 'http://purl.org/dc/dcmitype/PhysicalObject',
        'interactive_resource': 'http://purl.org/dc/dcmitype/InteractiveResource',
        'service': 'http://purl.org/dc/dcmitype/Service',
        'sound': 'http://purl.org/dc/dcmitype/Sound',
        'software': 'http://purl.org/dc/dcmitype/Software',
        'text': 'http://purl.org/dc/dcmitype/Text',
    },
    'encoding': 'UTF-8',
    'frequency' : 'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',
    'inspireid_theme': 'HB',
    'language': 'http://publications.europa.eu/resource/authority/language/ENG',
    'license': 'http://creativecommons.org/licenses/by/4.0/',
    'license_id': 'CC-BY-4.0',
    'license_url': 'https://publications.europa.eu/resource/authority/licence/CC_BY_4_0',
    'lineage_process_steps': 'Ministerio para la Transición Ecológica y el Reto Demográfico lineage process steps.',
    'maintainer_name': 'Ministerio para la Transición Ecológica y el Reto Demográfico',
    'maintainer_email': 'bzn-sig-miteco@miteco.es',
    'maintainer_url': 'https://www.miteco.gob.es/',
    'maintainer_uri': 'http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001/',
    'metadata_profile': [
        'http://semiceu.github.io/GeoDCAT-AP/releases/2.0.0','http://inspire.ec.europa.eu/document-tags/metadata'
    ],
    'miteco_geo_level': '6',
    'miteco_meth': ['https://semiceu.github.io/DCAT-AP/releases/3.0.0/'],
    'provenance': 'Ministerio para la Transición Ecológica y el Reto Demográfico provenance statement.',
    'publisher_name': 'Ministerio para la Transición Ecológica y el Reto Demográfico',
    'publisher_email': 'bzn-sig-miteco@miteco.es',
    'publisher_url': 'https://www.miteco.gob.es/',
    'publisher_identifier': 'https://www.miteco.gob.es/',
    'publisher_uri': 'http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001',
    'publisher_type': 'http://purl.org/adms/publishertype/NationalAuthority',
    'reference_system': 'http://www.opengis.net/def/crs/EPSG/0/4258',
    'representation_type': {
        'wfs': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/vector',
        'wcs': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/grid',
        'default': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/vector',
        'grid': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/grid',
        'vector': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/vector',
        'textTable': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/textTable',
        'tin': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/tin',
        'stereoModel': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/stereoModel',
        'video': 'http://inspire.ec.europa.eu/metadata-codelist/SpatialRepresentationType/video',
    },
    'resources': {
        'availability': 'http://publications.europa.eu/resource/authority/planned-availability/AVAILABLE',
        'name': {
            'es': 'Distribución {format}',
            'en': 'Distribution {format}'
        },
    },
    'rights': 'http://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess/noLimitations',
    'spatial': None,
    'spatial_uri': 'http://datos.gob.es/recurso/sector-publico/territorio/Pais/España',
    'status': 'http://purl.org/adms/status/UnderDevelopment',
    'temporal_start': '2025-01-01',
    'temporal_end': None,
    'theme': 'http://inspire.ec.europa.eu/theme/hb',
    'theme_es': 'http://datos.gob.es/kos/sector-publico/sector/medio-ambiente',
    'theme_eu': 'http://publications.europa.eu/resource/authority/data-theme/ENVI',
    'topic': 'http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/biota',
    'valid': None
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

RDF_DATASET_TEMPLATE = {
    "access_rights": "http://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess/noLimitations",
    "contact_email": "bzn-datos@miteco.es",
    "contact_name": "Ministerio para la Transición Ecológica y el Reto Demográfico",
    "contact_role": "http://inspire.ec.europa.eu/metadata-codelist/ResponsiblePartyRole/pointOfContact",
    "contact_uri": "http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001",
    "contact_url": "https://www.miteco.gob.es/",
    "dataset_scope": "spatial_dataset",
    "dcat_type": "http://inspire.ec.europa.eu/metadata-codelist/ResourceType/dataset",
    "language": "http://publications.europa.eu/resource/authority/language/SPA",
    "license_id": "CC-BY-4.0",
    "license_title": "Creative Commons Attribution 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "miteco_geo_level": "6",
    "publisher_email": "bzn-datos@miteco.es",
    "publisher_identifier": "http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001",
    "publisher_name": "Ministerio para la Transición Ecológica y el Reto Demográfico",
    "publisher_type": "http://purl.org/adms/publishertype/NationalAuthority",
    "publisher_uri": "https://catalogo.datosabiertos.miteco.gob.es/catalogo/organization/abogacia-del-estado",
    "publisher_url": "https://www.miteco.gob.es/",
    "spatial": "{\"type\": \"Polygon\", \"coordinates\": [[[-18.16, 27.64], [4.32, 27.64], [4.32, 43.79], [-18.16, 43.79], [-18.16, 27.64]]]}",
    "spatial_resolution_in_meters": "",
    "spatial_uri": "http://datos.gob.es/recurso/sector-publico/territorio/Pais/España",
    "state": "active",
    "type": "dataset",
    "theme_es": "http://datos.gob.es/kos/sector-publico/sector/medio-ambiente",
    "contact": [
      {
        "email": "bzn-datos@miteco.es",
        "name": "Ministerio para la Transición Ecológica y el Reto Demográfico",
        "role": "http://inspire.ec.europa.eu/metadata-codelist/ResponsiblePartyRole/pointOfContact",
        "uri": "http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001",
        "url": "https://www.miteco.gob.es/"
      }
    ],
    "publisher": [
      {
        "email": "bzn-datos@miteco.es",
        "identifier": "http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001",
        "name": "Ministerio para la Transición Ecológica y el Reto Demográfico",
        "type": "http://purl.org/adms/publishertype/NationalAuthority",
        "uri": "https://catalogo.datosabiertos.miteco.gob.es/catalogo/organization/abogacia-del-estado",
        "url": "https://www.miteco.gob.es/"
      }
    ],
  }
