"""Saved template previews must preserve the separately stored original XML."""
from unittest.mock import patch

import pytest
from ckan.plugins import toolkit
from ckanext.miteco.helpers import miteco_get_inspire_preview


def test_template_preview_renders_authorized_saved_metadata_without_persistence():
    unsaved = {'id': 'dataset-id', 'title': 'Unsaved title'}
    saved = {'id': 'dataset-id', 'title': 'Saved title'}
    with patch('ckanext.miteco.inspire.access.authorized_package', return_value=saved) as authorized, \
         patch('ckanext.miteco.inspire.generator.render_inspire_xml', return_value='<saved/>') as render, \
         patch('ckanext.miteco.helpers.miteco_get_inspire') as original, \
         patch('ckanext.miteco.inspire.access.find_document') as find, \
         patch('ckanext.miteco.inspire.model.setDocument') as persist:
        assert miteco_get_inspire_preview(unsaved, '<original/>', template=True) == '<saved/>'
        authorized.assert_called_once_with({}, 'dataset-id')
        render.assert_called_once_with(saved)
        original.assert_not_called()
        find.assert_not_called()
        persist.assert_not_called()
    assert unsaved['title'] == 'Unsaved title'


@pytest.mark.parametrize('error', [toolkit.NotAuthorized, toolkit.ObjectNotFound])
def test_template_preview_respects_read_permissions(error):
    with patch('ckanext.miteco.inspire.access.authorized_package', side_effect=error), \
         patch('ckanext.miteco.inspire.generator.render_inspire_xml') as render:
        assert miteco_get_inspire_preview({'id': 'private'}, '<original/>', template=True) == ''
        render.assert_not_called()


def test_template_preview_without_saved_identifier_is_empty():
    with patch('ckanext.miteco.inspire.access.authorized_package') as authorized:
        assert miteco_get_inspire_preview({'title': 'New'}, template=True) == ''
        authorized.assert_not_called()


def test_default_preview_preserves_original_without_rendering_or_persisting():
    original = '  <original/>\r\n'
    with patch('ckanext.miteco.inspire.generator.render_inspire_xml') as render, \
         patch('ckanext.miteco.inspire.model.setDocument') as persist:
        assert miteco_get_inspire_preview({'id': 'dataset-id'}, original) == original
        render.assert_not_called()
        persist.assert_not_called()
