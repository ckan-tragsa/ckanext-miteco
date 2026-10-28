import logging
from ckan.logic import side_effect_free, NotFound
from ckanext.miteco.inspire import model as insp_model
from ckanext.miteco.inspire import access

log = logging.getLogger(__name__)

@side_effect_free
def inspire_get_document(context, data_dict):
    """
    Retrieve a specific inspire document by its hash or UUID.

    Args:
        context (dict): The context of the API call.
        data_dict (dict): A dictionary containing the parameters for the API call.
            id (str): The ID of the document to retrieve
            hash (str): the hash of the specific version of the document to retrieve

    Returns:
        string: the raw XML string

    Example:
        To use this API, you can make a GET request to the following URL:
        ```
        http://<your-ckan-instance>/api/3/action/inspire_get_document?md5=<document md5>
        ```
    """
    uuid = data_dict.get('id',None)
    md5 = data_dict.get('hash',None)

    if not uuid and not md5:
        raise NotFound
    out = access.get_document(context, identifier=uuid, version=md5)
    if out:
        return insp_model.table_dictize(out, context)
    else:
        raise NotFound


@side_effect_free
def inspire_list_documents(context, data_dict):
    """
    Retrieve a list of all versions of a specific dataset or UUID.
    """
    target_id = data_dict.get('id', None)
    start = data_dict.get('start', 0)

    if not target_id or str(target_id).strip() in ('', 'None', 'new', 'null'):
        return []

    target_id = str(target_id).strip()
    package = access.authorized_package(context, target_id)
    valid_candidates = [value for value in (package.get('id'), package.get('name')) if value]

    out = insp_model.InspireHandler.list(candidates=valid_candidates, offset=start)
    raw_list = insp_model.table_dictize(out, context) if out else []

    # The hash identifies a stored version; elapsed time does not establish
    # content equivalence. Keep distinct versions, including rapid edits.
    seen = set()
    versions = []
    for item in raw_list:
        if item.get('md5') not in seen:
            seen.add(item.get('md5'))
            versions.append(item)
    return versions
