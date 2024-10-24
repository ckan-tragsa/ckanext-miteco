import logging
import typing
from collections import OrderedDict
from functools import partial

import ckan.plugins as p

from ckanext.miteco import helpers, validators, blueprint
import ckanext.miteco.logic.auth.ckan as ckan_auth

class MitecoPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IAuthFunctions)
    p.implements(p.IBlueprint)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IValidators)

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