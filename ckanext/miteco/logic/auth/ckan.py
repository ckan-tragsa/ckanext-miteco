import logging
import typing

import ckan.plugins.toolkit as toolkit
from ckan.logic.auth import get_package_object

logger = logging.getLogger(__name__)


@toolkit.chained_auth_function
def package_activity_list(next_auth, context, data_dict=None):
    try:
        toolkit.check_access("package_update", context, data_dict)
        return next_auth(context, data_dict)
    except toolkit.NotAuthorized:
        return {
            "success": False,
            "msg": toolkit._("User %s not authorized to see activity stream")
            % context.get("user", ""),
        }
