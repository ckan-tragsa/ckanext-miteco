import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
from flask import Blueprint
from flask import render_template
from flask import make_response
from ckanext.miteco import utils

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
