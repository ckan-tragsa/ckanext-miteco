# -*- coding: utf-8 -*-
"""
Tests for Inspire XML functionality (Sprint 1):
  - Logic Action: inspire_push_document (authorization, validation order, persistence)
  - Scheming Validator: miteco_iso_validator (XML syntax, INSPIRE schema, new dataset UUID)
  - Helper: miteco_get_inspire (handling raw XML strings and MD5 hashes)
  - Blueprint: dataset_inspire_xml and dataset_inspire_xml_version endpoints
"""
import pytest
from unittest.mock import MagicMock, patch

from ckantoolkit import ValidationError, NotAuthorized, missing as tk_missing
from ckan.tests import factories

from ckanext.miteco.inspire.logic.action.create import inspire_push_document, validate_insp
from ckanext.miteco.validators import miteco_iso_validator
from ckanext.miteco.helpers import miteco_get_inspire
from ckanext.miteco.inspire import model as insp_model


# Sample minimal ISO 19139 INSPIRE XML for testing
SAMPLE_VALID_INSPIRE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"
                 xmlns:gco="http://www.isotc211.org/2005/gco"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <gmd:fileIdentifier>
    <gco:CharacterString>test-uuid-12345</gco:CharacterString>
  </gmd:fileIdentifier>
  <gmd:language>
    <gmd:LanguageCode codeList="http://www.loc.gov/standards/iso639-2/" codeListValue="spa">spa</gmd:LanguageCode>
  </gmd:language>
  <gmd:characterSet>
    <gmd:MD_CharacterSetCode codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_CharacterSetCode" codeListValue="utf8">utf8</gmd:MD_CharacterSetCode>
  </gmd:characterSet>
</gmd:MD_Metadata>"""

SAMPLE_INVALID_SYNTAX_XML = "<gmd:MD_Metadata><unclosed_tag></gmd:MD_Metadata>"


# ── 1. Tests for inspire_push_document Action ────────────────────────────────

@pytest.mark.usefixtures("clean_db")
class TestInspirePushDocumentAction:

    def test_anonymous_user_raises_not_authorized(self):
        """Unauthenticated request must raise NotAuthorized without persisting XML."""
        context = {'user': None}
        data_dict = {'id': 'test-ds', 'xml': SAMPLE_VALID_INSPIRE_XML}

        with pytest.raises(NotAuthorized):
            inspire_push_document(context, data_dict)

    def test_missing_xml_raises_validation_error(self):
        """Missing or empty XML argument must raise ValidationError."""
        user = factories.User()
        context = {'user': user['name']}
        data_dict = {'id': 'test-ds', 'xml': ''}

        with pytest.raises(ValidationError):
            inspire_push_document(context, data_dict)

    @patch('ckanext.miteco.inspire.logic.action.create.validate_insp')
    @patch('ckanext.miteco.inspire.model.setDocument')
    def test_invalid_inspire_xml_does_not_persist_to_database(self, mock_set_doc, mock_validate):
        """Invalid INSPIRE XML must return failure and NEVER invoke setDocument."""
        mock_validate.return_value = (False, ['Missing mandatory INSPIRE elements'])

        user = factories.Sysadmin()
        dataset = factories.Dataset()
        context = {'user': user['name'], 'ignore_auth': True}
        data_dict = {'id': dataset['id'], 'xml': SAMPLE_VALID_INSPIRE_XML}

        result = inspire_push_document(context, data_dict)

        assert result['success'] is False
        assert 'Missing mandatory INSPIRE elements' in result['msg']
        mock_set_doc.assert_not_called()

    @patch('ckanext.miteco.inspire.logic.action.create.validate_insp')
    def test_valid_inspire_xml_persists_and_patches_dataset(self, mock_validate):
        """Valid XML must persist to inspire_xml and update dataset spatial_advanced_xml."""
        mock_validate.return_value = (True, [])

        user = factories.Sysadmin()
        dataset = factories.Dataset()
        context = {'user': user['name'], 'ignore_auth': True}
        data_dict = {'id': dataset['id'], 'xml': SAMPLE_VALID_INSPIRE_XML}

        result = inspire_push_document(context, data_dict)

        assert result['success'] is True
        assert 'md5' in result

        # Verify that dataset was patched with spatial_advanced_xml and is_spatial_advanced
        import ckan.plugins.toolkit as toolkit
        pkg = toolkit.get_action('package_show')(context, {'id': dataset['id']})
        assert pkg.get('is_spatial_advanced') == 'true'
        assert pkg.get('spatial_advanced_xml') == result['md5']


# ── 2. Tests for miteco_iso_validator (Scheming Validator) ───────────────────

class TestMitecoIsoValidator:

    def test_empty_or_missing_xml_is_ignored(self):
        """Validator should pass quietly when field is empty or missing."""
        val_func = miteco_iso_validator('spatial_advanced_xml', {})
        key = ('spatial_advanced_xml',)
        errors = {key: []}

        # Case: tk_missing
        data = {key: tk_missing}
        val_func(key, data, errors, {})
        assert len(errors[key]) == 0

        # Case: None or whitespace
        data = {key: '   '}
        val_func(key, data, errors, {})
        assert len(errors[key]) == 0

    def test_invalid_xml_syntax_appends_error(self):
        """Malformed XML syntax must report error without raising uncaught exceptions."""
        val_func = miteco_iso_validator('spatial_advanced_xml', {})
        key = ('spatial_advanced_xml',)
        data = {key: SAMPLE_INVALID_SYNTAX_XML}
        errors = {key: []}

        val_func(key, data, errors, {})

        assert len(errors[key]) > 0
        assert 'Invalid XML syntax' in errors[key][0]

    @patch('ckanext.spatial.harvesters.SpatialHarvester._get_validator')
    def test_invalid_inspire_schema_appends_error(self, mock_get_validator):
        """INSPIRE schema validation errors must be added to errors[key]."""
        mock_val_instance = MagicMock()
        mock_val_instance.is_valid.return_value = (False, 'iso19139', ['Missing gmd:contact'])
        mock_get_validator.return_value = mock_val_instance

        val_func = miteco_iso_validator('spatial_advanced_xml', {})
        key = ('spatial_advanced_xml',)
        data = {key: SAMPLE_VALID_INSPIRE_XML}
        errors = {key: []}

        val_func(key, data, errors, {})

        assert len(errors[key]) > 0
        assert any('Missing gmd:contact' in err for err in errors[key])

    @patch('ckanext.spatial.harvesters.SpatialHarvester._get_validator')
    @patch('ckanext.miteco.inspire.model.setDocument')
    def test_new_dataset_generates_uuid_and_persists(self, mock_set_doc, mock_get_validator):
        """On package_create where dataset id is not set, a UUID is assigned and persisted."""
        mock_val_instance = MagicMock()
        mock_val_instance.is_valid.return_value = (True, 'iso19139', [])
        mock_get_validator.return_value = mock_val_instance
        mock_set_doc.return_value = 'mocked_md5_hash'

        val_func = miteco_iso_validator('spatial_advanced_xml', {})
        key = ('spatial_advanced_xml',)
        data = {key: SAMPLE_VALID_INSPIRE_XML}  # Notice ('id',) is not set
        errors = {key: []}

        val_func(key, data, errors, {})

        assert len(errors[key]) == 0
        # A new UUID must have been assigned to data[('id',)]
        assert ('id',) in data
        assert len(data[('id',)]) == 36  # UUID standard length
        assert data.get(('is_spatial_advanced',)) == 'true'
        mock_set_doc.assert_called_once()


# ── 3. Tests for miteco_get_inspire Helper ───────────────────────────────────

class TestMitecoGetInspireHelper:

    def test_empty_input_returns_none(self):
        """Empty or falsy input returns None."""
        assert miteco_get_inspire(None) is None
        assert miteco_get_inspire('') is None

    def test_raw_xml_string_returns_itself(self):
        """When input is already a raw XML string, return it directly without DB lookup."""
        xml_input = "<gmd:MD_Metadata><test>content</test></gmd:MD_Metadata>"
        result = miteco_get_inspire(xml_input)
        assert result == xml_input

    @patch('ckan.plugins.toolkit.get_action')
    def test_md5_hash_retrieves_from_action(self, mock_get_action):
        """When input is an MD5 hash, retrieve raw XML via inspire_get_document."""
        mock_action = MagicMock()
        mock_action.return_value = {'xml': SAMPLE_VALID_INSPIRE_XML}
        mock_get_action.return_value = mock_action

        result = miteco_get_inspire('e59ff97941044f85df5297e1c302d260')

        assert result == SAMPLE_VALID_INSPIRE_XML
        mock_get_action.assert_called_with('inspire_get_document')


class TestMitecoHasInspireXmlHelper:

    def test_falsy_or_empty_package(self):
        from ckanext.miteco.helpers import miteco_has_inspire_xml
        assert miteco_has_inspire_xml(None) is False
        assert miteco_has_inspire_xml({}) is False

    def test_is_spatial_advanced_false(self):
        from ckanext.miteco.helpers import miteco_has_inspire_xml
        assert miteco_has_inspire_xml({'is_spatial_advanced': 'false', 'spatial_advanced_xml': 'abc'}) is False
        assert miteco_has_inspire_xml({'is_spatial_advanced': False, 'spatial_advanced_xml': 'abc'}) is False

    def test_spatial_advanced_xml_missing(self):
        from ckanext.miteco.helpers import miteco_has_inspire_xml
        assert miteco_has_inspire_xml({'is_spatial_advanced': 'true', 'spatial_advanced_xml': ''}) is False
        assert miteco_has_inspire_xml({'is_spatial_advanced': True, 'spatial_advanced_xml': None}) is False

    def test_valid_inspire_package(self):
        from ckanext.miteco.helpers import miteco_has_inspire_xml
        assert miteco_has_inspire_xml({'is_spatial_advanced': 'true', 'spatial_advanced_xml': 'hash123'}) is True
        assert miteco_has_inspire_xml({'is_spatial_advanced': True, 'spatial_advanced_xml': 'hash123'}) is True


class TestExtractMdMetadata:

    def test_pure_md_metadata_remains_unchanged(self):
        from ckanext.miteco.inspire.logic.action.create import extract_md_metadata
        assert extract_md_metadata(SAMPLE_VALID_INSPIRE_XML) == SAMPLE_VALID_INSPIRE_XML

    def test_csw_get_record_by_id_response_unwrapping(self):
        from ckanext.miteco.inspire.logic.action.create import extract_md_metadata
        csw_wrapped = f"""<csw:GetRecordByIdResponse xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">
{SAMPLE_VALID_INSPIRE_XML}
</csw:GetRecordByIdResponse>"""
        extracted = extract_md_metadata(csw_wrapped)
        assert "<csw:GetRecordByIdResponse" not in extracted
        assert "<gmd:MD_Metadata" in extracted
        assert "test-uuid-12345" in extracted


# ── 4. Tests for Blueprint XML Endpoints ─────────────────────────────────────

@pytest.mark.usefixtures("clean_db")
class TestInspireBlueprintEndpoints:

    def test_dataset_xml_endpoint_returns_xml(self, app):
        """GET /dataset/<id>/xml returns 200 with application/xml headers."""
        dataset = factories.Dataset()
        pk = insp_model.setDocument(dataset['id'], SAMPLE_VALID_INSPIRE_XML)

        # Patch dataset with spatial_advanced_xml
        import ckan.plugins.toolkit as toolkit
        toolkit.get_action('package_patch')(
            {'ignore_auth': True},
            {'id': dataset['id'], 'spatial_advanced_xml': pk, 'is_spatial_advanced': 'true'}
        )

        response = app.get(f"/dataset/{dataset['name']}/xml")

        assert response.status_code == 200
        assert 'application/xml' in response.headers.get('Content-Type', '')
        assert dataset['name'] in response.headers.get('Content-Disposition', '')
        assert '<gmd:MD_Metadata' in response.body.decode('utf-8')

    def test_dataset_xml_not_found(self, app):
        """GET /dataset/<id>/xml returns 404 if dataset has no stored XML."""
        dataset = factories.Dataset()
        response = app.get(f"/dataset/{dataset['name']}/xml", status=404)
        assert response.status_code == 404
