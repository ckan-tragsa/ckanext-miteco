"""A generated draft follows saved CKAN fields, independently of uploaded XML."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from flask import Flask
from jinja2 import Environment, FileSystemLoader
from lxml import etree

from ckanext.miteco import blueprint
from ckanext.miteco.inspire import generator

NS = {'gmd': 'http://www.isotc211.org/2005/gmd',
      'gco': 'http://www.isotc211.org/2005/gco'}


@pytest.mark.parametrize('stored', [None, SimpleNamespace(uuid='unit', xml='<original>España</original>')])
def test_template_reflects_saved_changes_without_rewriting_original(stored):
    templates = Path(generator.__file__).parents[1] / 'templates'
    environment = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
    package = {'id': 'unit', 'name': 'unit', 'title': 'Título inicial',
               'notes': 'Descripción inicial', 'spatial_advanced_xml': 'saved-hash',
               'is_spatial_advanced': True}

    def render(template, extra_vars):
        return environment.get_template(template).render(**extra_vars)

    app = Flask(__name__)
    with patch.object(blueprint, '_resolve_dataset', return_value=package), \
         patch.object(blueprint.access, 'find_document', return_value=stored) as find, \
         patch.object(generator.toolkit, 'render', side_effect=render), \
         patch.object(generator.insp_model, 'setDocument') as save:
        for title, notes in [('Título inicial', 'Descripción inicial'),
                             ('España & agua actualizada', 'Descripción nueva <editada>')]:
            package.update(title=title, notes=notes)
            with app.test_request_context('/dataset/unit/xml?template=true&download=true'):
                response = blueprint.dataset_inspire_xml('unit')
            tree = etree.fromstring(response.get_data())
            assert tree.xpath('string(//gmd:identificationInfo/*/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString)', namespaces=NS) == title
            assert tree.xpath('string(//gmd:identificationInfo/*/gmd:abstract/gco:CharacterString)', namespaces=NS) == notes
            assert response.headers['Content-Disposition'].startswith('attachment')
        find.assert_not_called()
        save.assert_not_called()
        if stored:
            with app.test_request_context('/dataset/unit/xml?download=true'):
                assert blueprint.dataset_inspire_xml('unit').get_data() == stored.xml.encode('utf-8')
            save.assert_not_called()


def test_template_checks_package_access_before_rendering():
    from werkzeug.exceptions import Forbidden
    with Flask(__name__).test_request_context('/dataset/private/xml?template=true'), \
         patch.object(blueprint.access, 'authorized_package', side_effect=blueprint.logic.NotAuthorized), \
         patch.object(generator, 'render_inspire_xml') as render:
        with pytest.raises(Forbidden):
            blueprint.dataset_inspire_xml('private')
        render.assert_not_called()
