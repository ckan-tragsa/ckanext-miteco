import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
from flask import Blueprint, render_template, make_response, abort, request  # type: ignore
from ckanext.miteco import utils
from ckanext.inspire.download import dataset_inspire_xml, dataset_inspire_xml_version

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


miteco.add_url_rule('/dataset/<_id>/xml', view_func=dataset_inspire_xml)
miteco.add_url_rule('/dataset/<_id>/xml/<_hash>', view_func=dataset_inspire_xml_version)
