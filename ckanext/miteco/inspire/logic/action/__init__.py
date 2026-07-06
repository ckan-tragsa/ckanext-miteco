from inspect import getmembers, isfunction
import logging
from ckanext.miteco.inspire.logic.action import create, delete, get, patch, update
log = logging.getLogger(__name__)

try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

all_calls = {}

def api_call(fn):
    """
    collect call functions into ckanext.miteco.all_calls dict
    """
    all_calls[fn.__name__] = fn
    return fn

for call_type in [create,delete,get,patch,update]:
    for function in getmembers(call_type, isfunction):
        log.debug(function[0][0:7])
        if "inspire" in function[0]:
            log.debug(f"added {function[0]} to api_call")
            api_call(function[1])

