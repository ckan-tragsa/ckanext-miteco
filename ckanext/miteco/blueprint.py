import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
from flask import Blueprint, render_template, make_response, abort, request  # type: ignore
from ckanext.miteco import utils
from ckanext.miteco.inspire import model as insp_model

from logging import getLogger

logger = getLogger(__name__)
get_action = logic.get_action

miteco = Blueprint(u'miteco', __name__)

def tags():
    return render_template('home/tags.html')

miteco.add_url_rule('/miteco/tags/', view_func=tags)


#ESTAS FUNCIONES DEVUELVEN COMO TAL EL SERIALIZADO
def catalog_atom():
    atom = utils.catalog_atom_page()

    response = make_response(atom)
    response.headers["Content-Type"] = "application/atom+xml"

    return response


def dataset_atom(_id):
    atom = utils.dataset_atom_page(_id)

    response = make_response(atom)
    response.headers["Content-Type"] = "application/atom+xml"

    return response

# 1 regla para el catalogo y otra para el dataset, cada una con su función correspondiente. 
# La función catalog_atom genera el feed ATOM para el catálogo completo, mientras que dataset_atom genera el feed ATOM para un dataset específico identificado por su ID. Ambas funciones devuelven la respuesta HTTP con el contenido del feed y el tipo de contenido adecuado.
miteco.add_url_rule('/miteco/catalog.atom', view_func=catalog_atom)
miteco.add_url_rule('/miteco/dataset/<_id>.atom', view_func=dataset_atom)


# ── Inspire XML endpoints ────────────────────────────────────────────────────

def _resolve_dataset(_id):
    """
    Given a dataset slug or UUID, returns the package dict.
    Raises 404 if the dataset does not exist or 403 if user cannot read it.
    """
    try:
        context = {'ignore_auth': False}
        return get_action('package_show')(context, {'id': _id})
    except logic.NotFound:
        abort(404)
    except logic.NotAuthorized:
        abort(403)


def _resolve_dataset_uuid(_id):
    """
    Given a dataset slug or UUID, returns the canonical UUID.
    """
    pkg = _resolve_dataset(_id)
    return pkg['id']


def dataset_inspire_xml(_id):
    """
    Returns the latest stored Inspire XML document for a dataset.

    GET /dataset/<slug-or-uuid>/xml
    """
    pkg = _resolve_dataset(_id)
    uuid = pkg['id']

    doc = insp_model.InspireHandler.get(uuid=uuid)
    if not doc and pkg.get('spatial_advanced_xml'):
        doc = insp_model.InspireHandler.get(md5=pkg['spatial_advanced_xml'])

    if not doc:
        abort(404)

    is_download = request.args.get('download', 'false').lower() in ('true', '1')
    disposition = 'attachment' if is_download else 'inline'

    response = make_response(doc.xml)
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    response.headers['Content-Disposition'] = (
        '{}; filename="{}.xml"'.format(disposition, _id)
    )
    return response


def dataset_inspire_xml_version(_id, _hash):
    """
    Returns a specific version of the Inspire XML document identified by its md5 hash.

    GET /dataset/<slug-or-uuid>/xml/<md5-hash>
    """
    _resolve_dataset_uuid(_id)  # authorisation + existence check

    doc = insp_model.InspireHandler.get(md5=_hash)
    if not doc:
        abort(404)

    is_download = request.args.get('download', 'false').lower() in ('true', '1')
    disposition = 'attachment' if is_download else 'inline'

    response = make_response(doc.xml)
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    response.headers['Content-Disposition'] = (
        '{}; filename="{}-{}.xml"'.format(disposition, _id, _hash[:8])
    )
    return response


miteco.add_url_rule('/dataset/<_id>/xml', view_func=dataset_inspire_xml)
miteco.add_url_rule('/dataset/<_id>/xml/<_hash>', view_func=dataset_inspire_xml_version)
