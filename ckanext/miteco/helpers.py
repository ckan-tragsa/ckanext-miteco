import json
import logging
import typing
from functools import lru_cache

import ckan.lib.helpers as h
import ckan.plugins as p
import ckan.authz as authz
from ckan import model
import ckan.logic as logic

log = logging.getLogger(__name__)

all_helpers = {}

def helper(fn):
    """Collect helper functions into the ckanext.schemingdcat.all_helpers dictionary.

    Args:
        fn (function): The helper function to add to the dictionary.

    Returns:
        function: The helper function.
    """
    all_helpers[fn.__name__] = fn
    return fn

@helper
def miteco_check_miteco_identifier(miteco_identifier):
    '''
    Returns the current package count for datasets associated with the given
    source id
    '''
    fq = '+extras_miteco_identifier:"{0}"'.format(miteco_identifier)
    search_dict = {'fq': fq, 'include_private': True}
    context = {'model': model, 'session': model.Session}
    result = logic.get_action('package_search')(context, search_dict)
    return result.get('count', 0)
