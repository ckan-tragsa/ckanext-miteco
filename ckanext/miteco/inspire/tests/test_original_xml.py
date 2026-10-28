"""Stored uploads are independent of CKAN's editable fields."""
from types import SimpleNamespace
from unittest.mock import patch
from flask import Flask

XML = '\ufeff<?xml version="1.0" encoding="UTF-8"?>\r\n<original>España</original>\r\n'


def test_download_returns_stored_text_without_synchronizing():
    from ckanext.miteco.blueprint import dataset_inspire_xml
    with Flask(__name__).test_request_context('/dataset/unit/xml?download=true'), \
         patch('ckanext.miteco.blueprint._resolve_dataset', return_value={'id':'unit','spatial_advanced_xml':'hash','title':'Different'}), \
         patch('ckanext.miteco.inspire.model.InspireHandler.get', return_value=SimpleNamespace(uuid="unit", xml=XML)), \
         patch('ckanext.miteco.inspire.generator.sync_xml_with_package') as sync:
        response = dataset_inspire_xml('unit')
        assert response.get_data() == XML.encode('utf-8')
        assert response.headers['Content-Disposition'].startswith('attachment')
        sync.assert_not_called()


def test_preview_uses_stored_document_without_generated_values():
    from ckanext.miteco.helpers import miteco_get_inspire_preview
    with patch('ckanext.miteco.inspire.model.InspireHandler.get', return_value=SimpleNamespace(uuid="unit", xml=XML)), \
         patch('ckanext.miteco.inspire.generator.sync_xml_with_package') as sync:
        assert miteco_get_inspire_preview({'id':'unit','spatial_advanced_xml':'hash','title':'Different'}) == XML
        sync.assert_not_called()


def test_edit_hook_does_not_rewrite_existing_xml():
    from ckanext.miteco.plugin import InspirePlugin
    with patch('ckanext.miteco.inspire.model.setDocument') as save, \
         patch('ckanext.miteco.inspire.generator.sync_xml_with_package') as sync, \
         patch('ckanext.miteco.inspire.generator.generate_inspire_xml') as generate:
        InspirePlugin._ensure_inspire_xml(None, {}, {'id':'unit','spatial_advanced_xml':'hash','is_spatial_advanced':True,'title':'Different'})
        save.assert_not_called()
        sync.assert_not_called()
        generate.assert_not_called()
