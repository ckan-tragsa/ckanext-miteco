"""Focused regressions without CKAN database fixtures."""
from unittest.mock import patch
from lxml import etree
from ckanext.miteco.inspire.merge import has_text, merge_resources
from ckanext.miteco.inspire.generator import sync_xml_with_package


def test_empty_multilingual_is_not_source_content():
    assert not has_text({'es': '', 'en': '  '})
    assert has_text({'es': 'Notas'})
    assert has_text(0) and has_text(False)


def test_resource_identity_survives_reordering():
    old = [{'id': 'a', 'url': 'https://example.invalid/a', 'name': 'A'},
           {'id': 'b', 'url': 'https://example.invalid/b', 'name': 'B'}]
    imported = [{'url': x['url'], 'name': x['name']} for x in reversed(old)]
    assert [x['id'] for x in merge_resources(old, imported, True)] == ['b', 'a']
    assert merge_resources(old, imported, False) == old


def test_same_endpoint_different_operations_are_distinct():
    old = [{'id': 'a', 'url': 'https://example.invalid/wms', 'name': 'A'},
           {'id': 'b', 'url': 'https://example.invalid/wms', 'name': 'B'}]
    imported = [{'url': x['url'], 'name': x['name']} for x in old]
    assert [x['id'] for x in merge_resources(old, imported, True)] == ['a', 'b']


def test_ambiguous_identity_is_rejected():
    old = [{'id': 'a', 'url': 'x', 'name': 'same'}, {'id': 'b', 'url': 'x', 'name': 'same'}]
    try:
        merge_resources(old, [{'url': 'x', 'name': 'same'}], True)
    except ValueError:
        return
    raise AssertionError('Ambiguous identity accepted')


def test_new_resource_gets_no_reused_id():
    assert 'id' not in merge_resources([], [{'id': 'untrusted', 'url': 'x'}], True)[0]


XML = '<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gco="http://www.isotc211.org/2005/gco"><gmd:dateStamp><gco:DateTime>2020-01-01T12:00:00Z</gco:DateTime></gmd:dateStamp><gmd:identificationInfo><gmd:MD_DataIdentification><gmd:citation><gmd:CI_Citation><gmd:title><gco:CharacterString>Original</gco:CharacterString></gmd:title></gmd:CI_Citation></gmd:citation><gmd:supplementalInformation><gco:CharacterString>España: conservar</gco:CharacterString></gmd:supplementalInformation></gmd:MD_DataIdentification></gmd:identificationInfo></gmd:MD_Metadata>'


@patch('ckanext.miteco.inspire.generator.validate_insp', return_value=(True, []))
def test_sync_is_noop_without_edits(validate):
    assert sync_xml_with_package(XML, {'title': 'Original'}) == XML
    validate.assert_not_called()


@patch('ckanext.miteco.inspire.generator.validate_insp', return_value=(True, []))
def test_sync_keeps_unmapped_content_and_valid_datetime(validate):
    from datetime import datetime
    result = sync_xml_with_package(XML, {'title': 'Nuevo'})
    root = etree.fromstring(result.encode())
    dt = root.xpath('//*[local-name()="DateTime"]')[0].text
    datetime.fromisoformat(dt.replace('Z', '+00:00'))
    assert 'T' in dt
    assert root.xpath('//*[local-name()="title"]/*/text()') == ['Nuevo']
    validate.assert_called_once()
    assert 'España: conservar' in result
    assert sync_xml_with_package(result, {'title': 'Nuevo'}) == result


@patch('ckanext.miteco.inspire.generator.validate_insp', return_value=(False, ['invalid']))
def test_invalid_sync_keeps_original(validate):
    assert sync_xml_with_package(XML, {'title': 'Nuevo'}) == XML
    validate.assert_called_once()


def test_resource_defaults_do_not_change_identity():
    old = [{'id': 'a', 'url': 'https://example.invalid/data.zip', 'format': 'ZIP',
            'download_url': 'https://example.invalid/data.zip'}]
    assert merge_resources(old, [{'url': old[0]['url']}], True)[0]['id'] == 'a'


def test_local_adapters_delegate_outside_import_context():
    from ckanext.miteco.inspire.schema import _adapt_validator
    calls = []
    def original(key, data, errors, context):
        calls.append((key, data, errors, context))
        return 'original-result'
    for name in ('schemingdcat_dataset_url', 'schemingdcat_if_empty_datenow',
                 'schemingdcat_contact_as_default_publisher', 'schemingdcat_fill_dependent_fields'):
        adapted = _adapt_validator(original, {}, name)
        data, errors, context = {}, {}, {}
        assert adapted(('x',), data, errors, context) == 'original-result'
        assert calls[-1] == (('x',), data, errors, context)


def test_rapid_distinct_versions_are_not_hidden():
    from ckanext.miteco.inspire.logic.action.get import inspire_list_documents
    rows = [{'md5': 'a', 'time': '2026-10-26T10:00:00Z'},
            {'md5': 'b', 'time': '2026-10-26T10:00:01Z'}]
    with patch('ckanext.miteco.inspire.access.authorized_package', return_value={'id': 'synthetic', 'name': 'synthetic'}), \
         patch('ckanext.miteco.inspire.model.InspireHandler.list', return_value=rows), \
         patch('ckanext.miteco.inspire.model.table_dictize', return_value=rows):
        assert inspire_list_documents({}, {'id': 'synthetic'}) == rows


def test_different_operation_is_not_matched_by_url_alone():
    old = [{'id': 'a', 'url': 'https://example.invalid/wms', 'name': 'Operation A'}]
    result = merge_resources(old, [{'url': old[0]['url'], 'name': 'Operation B'}], False)
    assert len(result) == 2 and 'id' not in result[1]
