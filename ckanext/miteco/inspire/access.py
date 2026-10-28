"""Authorize XML access through its owning CKAN package, never through a hash."""
from ckan.logic import NotFound
from ckan.plugins import toolkit
from ckanext.miteco.inspire import model as insp_model


def authorized_package(context, identifier):
    """Resolve UUID/slug with CKAN's package permissions and request identity."""
    local = dict(context)
    if 'user' not in local:
        try:
            local['user'] = getattr(toolkit.g, 'user', None)
            local['auth_user_obj'] = getattr(toolkit.g, 'userobj', None)
        except RuntimeError:
            local['user'] = None
    return toolkit.get_action('package_show')(local, {'id': identifier})


def find_document(package, version=None):
    """Find XML belonging to this package; callers authorize before exposure.

    Accept the canonical ID and current legacy slug. An explicit version must
    match this package and must never fall back to another stored document.
    """
    owners = {str(value) for value in (package.get('id'), package.get('name')) if value}

    def belongs(document):
        return document is not None and str(document.uuid) in owners

    if version:
        document = insp_model.InspireHandler.get(md5=version)
        return document if belongs(document) else None
    key = package.get('spatial_advanced_xml')
    if key:
        document = insp_model.InspireHandler.get(md5=key)
        if belongs(document):
            return document
    for owner in (package.get('id'), package.get('name')):
        if owner:
            document = insp_model.InspireHandler.get(uuid=owner)
            if belongs(document):
                return document
    return None


def get_document(context, identifier=None, version=None):
    """Resolve an XML version only after authorizing its owning package."""
    if identifier:
        package = authorized_package(context, identifier)
        document = find_document(package, version)
    elif version:
        document = insp_model.InspireHandler.get(md5=version)
        if document is None or not document.uuid:
            raise NotFound
        package = authorized_package(context, document.uuid)
        if str(document.uuid) not in {str(package.get('id')), str(package.get('name'))}:
            raise NotFound
    else:
        raise NotFound
    if document is None:
        raise NotFound
    return document
