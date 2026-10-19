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
    Retrieve a list of all versions of a specific dataset or UUID.
    """
    target_id = data_dict.get('id', None)
    start = data_dict.get('start', 0)

    candidates = set()
    if target_id:
        candidates.add(str(target_id))
        try:
            from ckan import model
            pkg = model.Package.get(target_id)
            if pkg:
                if pkg.id:
                    candidates.add(str(pkg.id))
                if pkg.name:
                    candidates.add(str(pkg.name))
                # Si el paquete tiene un hash MD5 asociado, buscar también el registro del documento
                if getattr(pkg, 'spatial_advanced_xml', None):
                    cur_doc = insp_model.InspireHandler.get(md5=pkg.spatial_advanced_xml)
                    if cur_doc and cur_doc.uuid:
                        candidates.add(str(cur_doc.uuid))
        except Exception:
            pass

    out = insp_model.InspireHandler.list(candidates=list(candidates), offset=start)
    return insp_model.table_dictize(out, context) if out else []

