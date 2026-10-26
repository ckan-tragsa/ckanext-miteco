import pytest
from unittest.mock import patch, MagicMock
from ckanext.miteco.inspire.generator import (
    build_inspire_record,
    render_inspire_xml,
    generate_inspire_xml,
    _extract_bbox_from_geojson,
    _clean_topic_category
)
from ckanext.miteco.inspire.logic.action.create import validate_insp


def test_clean_topic_category():
    assert _clean_topic_category('environment') == 'environment'
    assert _clean_topic_category('http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/biota') == 'biota'
    assert _clean_topic_category('unknown_invalid_topic') == 'environment'
    assert _clean_topic_category(None) == 'environment'


def test_extract_bbox_from_geojson():
    geojson_poly = {
        "type": "Polygon",
        "coordinates": [[[-3.7, 40.4], [-3.6, 40.4], [-3.6, 40.5], [-3.7, 40.5], [-3.7, 40.4]]]
    }
    bbox = _extract_bbox_from_geojson(geojson_poly)
    assert bbox == [-3.7, 40.4, -3.6, 40.5]

    assert _extract_bbox_from_geojson(None) is None
    assert _extract_bbox_from_geojson("invalid json") is None


def test_build_inspire_record_dataset():
    pkg = {
        'id': 'test-ds-1',
        'name': 'test-dataset-miteco',
        'title': 'Dataset de Prueba MITECO',
        'notes': 'Descripción detallada para la prueba de metadatos INSPIRE.',
        'topic': 'http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/environment',
        'publisher_name': 'MITECO Test Org',
        'publisher_email': 'test@miteco.es',
        'tags': [{'name': 'medio-ambiente'}, {'name': 'espacial'}],
        'resources': [
            {'name': 'Capa Shapefile', 'url': 'https://example.com/data.zip', 'format': 'SHP'}
        ]
    }
    record = build_inspire_record(pkg)
    assert record['metadata']['identifier'] == 'test-ds-1'
    assert record['metadata']['hierarchylevel']['value'] == 'dataset'
    assert record['identification']['title'] == 'Dataset de Prueba MITECO'
    assert record['identification']['topiccategory'] == ['environment']
    assert record['contact']['pointOfContact']['organization'] == 'MITECO Test Org'
    assert len(record['distribution']) == 1


def test_build_inspire_record_service():
    pkg = {
        'id': 'test-srv-1',
        'name': 'test-service-wms',
        'title': 'Servicio WMS de Cartografía',
        'notes': 'Servicio de mapas OGC WMS de prueba.',
        'dcat_type': 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/service',
        'publisher_name': 'MITECO SIG',
        'publisher_email': 'sig@miteco.es',
        'resources': [
            {'name': 'GetCapabilities', 'url': 'https://example.com/wms?request=GetCapabilities', 'format': 'WMS'}
        ]
    }
    record = build_inspire_record(pkg)
    assert record['metadata']['hierarchylevel']['value'] == 'service'
    assert record['identification']['service_type'] == 'OGC:WMS'


@patch('ckan.plugins.toolkit.render')
def test_generate_inspire_xml_preserves_existing_user_xml(mock_render):
    pkg = {
        'id': 'existing-pkg-id',
        'name': 'existing-pkg',
        'is_spatial_advanced': 'true',
        'spatial_advanced_xml': 'abc123md5hash'
    }
    mock_doc = MagicMock()
    mock_doc.xml = '<gmd:MD_Metadata><userUploaded>true</userUploaded></gmd:MD_Metadata>'

    with patch('ckanext.miteco.inspire.model.InspireHandler.get', return_value=mock_doc):
        success, result_xml, errors = generate_inspire_xml(pkg, persist=False)
        assert success is True
        assert result_xml == mock_doc.xml
        assert errors == []
        mock_render.assert_not_called()
