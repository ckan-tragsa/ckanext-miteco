import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
from flask import Blueprint
from flask import render_template
from flask import make_response
from ckanext.miteco import utils

from logging import getLogger

logger = getLogger(__name__)

inspire = Blueprint(u'inspire', __name__,
                    url_prefix=u'/inspire')

@inspire.route(u'/dataset/new',defaults={'id':''})
@inspire.route(u'/dataset/<id>')
def inspire_form(id):
    try:
        package = toolkit.get_action("package_get")({"id":id})
        package['Type'] = 'dataset'
    except:
        package = {}

    return toolkit.render('miteco/inspire.html',extra_vars={u'pkg_dict':package,
                                                            u'form_vars':{u'field':{u'field_name':"spatial_advanced_xml"}},
                                                            u'form_snippet':u'schemingdcat/form_snippets/inspire_xml.html',
                                                            })






