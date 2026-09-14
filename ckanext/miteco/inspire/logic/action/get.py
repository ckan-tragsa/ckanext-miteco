from ckan.logic import side_effect_free, NotFound
from ckanext.miteco.inspire import model as insp_model

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
    out = insp_model.InspireHandler.get(uuid=uuid, md5=md5)
    if out:
        return insp_model.table_dictize(out, context)
    else:
        raise NotFound


@side_effect_free
def inspire_list_documents(context, data_dict):
    """
    Retrieve a list of all versions of a specific UUID.

    Args:
        context (dict): The context of the API call.
        data_dict (dict): A dictionary containing the parameters for the API call.
            id (str): The ID of the document to retrieve
            start (int): offset of docuements to retrieve

    Returns:
        list: the raw XML string

    Example:
        To use this API, you can make a GET request to the following URL:
        ```
        http://<your-ckan-instance>/api/3/action/inspire_list_documents?id=<document UUID>
        ```
    """
    uuid = data_dict.get('id', None)
    start = data_dict.get('start', 0)

    out = insp_model.InspireHandler.list(uuid=uuid, offset=start)
    return insp_model.table_dictize(out, context) if out else []

