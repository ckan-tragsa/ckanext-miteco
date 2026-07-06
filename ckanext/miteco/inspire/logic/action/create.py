from ckanext.miteco.inspire import model as insp_model
import ckan.plugins as p
from ckan import model


def inspire_push_document(context, data_dict):
    """
    push a XML document into the database

    Args:
        context (dict): The context of the API call.
        data_dict (dict): A dictionary containing the parameters for the API call.
            id (str): The ID of the document to retrieve
            xml (str): The XML to store

    Returns:

    Example:
        To use this API, you can make a GET request to the following URL:
        ```
        http://<your-ckan-instance>/api/3/action/inspire_push_document?md5=<document md5>
        ```
    """
    # Authorization: Only sysadmins can reset statistics
    user = context.get('user')
    if not user:
        raise p.toolkit.NotAuthorized('User must be logged in to reset statistics.')

    user_obj = model.User.get(user)
    if not user_obj or not user_obj.sysadmin:
        raise p.toolkit.NotAuthorized('User %s not authorized to reset statistics. Only SysAdmins', user)

    uuid = data_dict.get('id')
    xml = data_dict.get('xml')
    insp_model.setDocument(uuid,xml)

    return {'success': True, 'msg': 'xml loaded.'}