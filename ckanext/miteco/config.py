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