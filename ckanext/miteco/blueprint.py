import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
from flask import Blueprint

from logging import getLogger

logger = getLogger(__name__)
get_action = logic.get_action

miteco = Blueprint(u'miteco', __name__)