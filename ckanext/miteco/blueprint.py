import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
from flask import Blueprint
from flask import render_template

from logging import getLogger

logger = getLogger(__name__)
get_action = logic.get_action

miteco = Blueprint(u'miteco', __name__)

def tags():
    return render_template('home/tags.html')

miteco.add_url_rule('/miteco/tags/', view_func=tags)