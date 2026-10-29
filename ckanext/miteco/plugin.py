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
import ckanext.miteco.inspire.blueprint as insp_blueprint
import ckanext.miteco.inspire.logic.action as inspire_api
import ckanext.miteco.config as miteco_config
from ckanext.miteco.validation.validation import ISO19139InspireSchema as inspireValidator
from ckanext.miteco.lib.rdfParser import mitecoRDFParser
from ckanext.spatial.interfaces import ISpatialHarvester


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
        return {
            "package_activity_list": ckan_auth.package_activity_list,
        }

    # Blueprints
    def get_blueprint(self):
        return [blueprint.miteco, insp_blueprint.inspire]

    # Helpers
    def get_helpers(self):
        all_helpers = dict(helpers.all_helpers)
        return all_helpers

    # Validators
    def get_validators(self):
        from ckanext.miteco.inspire.schema import get_import_validators
        registered = dict(validators.all_validators)
        registered.update(get_import_validators())
        return registered
    
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
    p.implements(ISpatialHarvester)
    p.implements(p.IPackageController, inherit=True)

    #IConfigurable
    def configure(self, config):
        miteco_config.miteco_rdf_parser = mitecoRDFParser() 
        insp_model.setup()

    #IActions
    def get_actions(self):
        log.debug(inspire_api.all_calls)
        return dict(inspire_api.all_calls)

    #ISpatialHarvester
    def get_package_dict(self, context, data_dict):
        return data_dict['package_dict']

    def get_validators(self):
        return [inspireValidator]

    def transform_to_iso(self, original_document, original_format, harvest_object):
        return None

    # IPackageController
    def after_dataset_create(self, context, data_dict):
        self._ensure_inspire_xml(context, data_dict)

    def after_dataset_update(self, context, data_dict):
        self._ensure_inspire_xml(context, data_dict)

    def _ensure_inspire_xml(self, context, data_dict):
        if not data_dict:
            return
        if context and context.get('_inspire_pushing'):
            return
        # Editing CKAN fields must not rewrite an existing XML document.
        xml_key = data_dict.get('spatial_advanced_xml')
        is_adv = data_dict.get('is_spatial_advanced')
        if not xml_key and 'extras' in data_dict:
            for extra in data_dict.get('extras') or []:
                if isinstance(extra, dict):
                    if extra.get('key') == 'spatial_advanced_xml':
                        xml_key = extra.get('value')
                    elif extra.get('key') == 'is_spatial_advanced':
                        is_adv = extra.get('value')

        if xml_key and (p.toolkit.asbool(is_adv) or str(xml_key).strip()):
            return

        dcat_type = str(data_dict.get('dcat_type') or '').lower()
        is_spatial = (
            'geospatial' in dcat_type or
            'dataset' in dcat_type or
            'service' in dcat_type or
            data_dict.get('type') == 'service' or
            data_dict.get('spatial') or
            data_dict.get('spatial_uri')
        )
        if not is_spatial:
            return

        try:
            from ckanext.miteco.inspire.generator import generate_inspire_xml
            success, res, errors = generate_inspire_xml(data_dict, persist=True)
            if success:
                log.info(f"Auto-generated and persisted INSPIRE XML for package {data_dict.get('name')}: {res}")
        except Exception as e:
            log.warning(f"Could not auto-generate INSPIRE XML for package {data_dict.get('name')}: {e}")
 
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

