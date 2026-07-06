import sys
import logging
import typing
import importlib
import inspect

import ckan.plugins as p
from ckan.lib.plugins import DefaultTranslation
from ckan import logic

from ckanext.miteco import helpers, validators, blueprint, config
import ckanext.miteco.logic.auth.ckan as ckan_auth 
import ckanext.miteco.inspire.model as insp_model
import ckanext.miteco.inspire.logic.action as inspire_api


log = logging.getLogger(__name__)

try:
    config_declarations = p.toolkit.blanket.config_declarations
except AttributeError:
    # CKAN 2.9 does not have config_declarations.
    # Remove when dropping support.
    def config_declarations(cls):
        return cls

@config_declarations
class MitecoPlugin(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IBlueprint)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IValidators)
    p.implements(p.ITranslation) 

    # IConfigurer
    def update_config(self, config_):
        p.toolkit.add_template_directory(config_, 'templates')
        p.toolkit.add_public_directory(config_, 'public')
        p.toolkit.add_resource("assets", "ckanext-miteco")

    # Auth functions
    def get_auth_functions(self) -> typing.Dict[str, typing.Callable]:
        return {}

    # Blueprints
    def get_blueprint(self):
        return [blueprint.miteco]

    # Helpers
    def get_helpers(self):
        all_helpers = dict(helpers.all_helpers)
        return all_helpers

    # Validators
    def get_validators(self):
        return dict(validators.all_validators)
    
    # IActions
    def get_actions(self):
        module_root = 'ckanext.miteco.logic.action'
        action_functions = _get_logic_functions(module_root)

        return action_functions
'''
def _get_logic_functions(module_root, logic_functions={}):

    for module_name in ['get', 'create', 'update', 'patch', 'delete']:
        module_path = '%s.%s' % (module_root, module_name,)

        module = __import__(module_path)

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)

        for key, value in module.__dict__.items():
            if not key.startswith('_') and (hasattr(value, '__call__')
                                            and (value.__module__ == module_path)):
                logic_functions[key] = value

    return logic_functions
    '''

class InspirePlugin(p.SingletonPlugin, DefaultTranslation):
    p.implements(p.IActions)
    p.implements(p.IConfigurable)

    #IConfigurable
    def configure(self, config):
        insp_model.setup()

    #IActions
    def get_actions(self):
        log.debug(inspire_api.all_calls)
        return dict(inspire_api.all_calls)
 
def _get_logic_functions(module_root, logic_functions=None, decorator=None):
    """
    Retrieves and aggregates logic functions from specified submodules, filtering by decorator.

    This function dynamically imports submodules ('get', 'create', 'update', 'patch', 'delete')
    from the given `module_root`. It then extracts callable functions from these submodules
    that do not start with an underscore, belong to the submodule's namespace, and are decorated
    with the specified decorator. These functions are added to the `logic_functions` dictionary.

    Args:
        module_root (str): The root module path from which to import submodules.
        logic_functions (dict, optional): A dictionary to store the aggregated logic functions.
            Defaults to None, which initializes an empty dictionary.
        decorator (callable, optional): A decorator function to filter the logic functions.
            Only functions decorated with this decorator will be imported. Defaults to None.

    Returns:
        dict: A dictionary containing the aggregated and filtered logic functions.
    """
    if logic_functions is None:
        logic_functions = {}

    for module_name in ['get', 'create', 'update', 'patch', 'delete']:
        module_path = f"{module_root}.{module_name}"

        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            log.error(f"Error importing module {module_path}: {e}")
            continue

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith('_'):
                if decorator is None or getattr(obj, 'is_decorated_with_action', False):
                    logic_functions[name] = obj

    return logic_functions