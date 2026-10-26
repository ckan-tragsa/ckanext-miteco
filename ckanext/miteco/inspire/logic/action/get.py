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

    if not target_id or str(target_id).strip() in ('', 'None', 'new', 'null'):
        return []

    target_id = str(target_id).strip()
    candidates = set()
    candidates.add(target_id)
    try:
        from ckan import model
        pkg = model.Package.get(target_id)
        if pkg:
            if pkg.id:
                candidates.add(str(pkg.id).strip())
            if pkg.name:
                candidates.add(str(pkg.name).strip())
            for extra in getattr(pkg, 'extras_list', []):
                if getattr(extra, 'key', '') == 'spatial_advanced_xml' and extra.value:
                    cur_doc = insp_model.InspireHandler.get(md5=extra.value)
                    if cur_doc and cur_doc.uuid:
                        candidates.add(str(cur_doc.uuid).strip())
            if hasattr(pkg, 'spatial_advanced_xml') and pkg.spatial_advanced_xml:
                cur_doc = insp_model.InspireHandler.get(md5=pkg.spatial_advanced_xml)
                if cur_doc and cur_doc.uuid:
                    candidates.add(str(cur_doc.uuid).strip())
    except Exception as e:
        log.warning(f"Error resolving candidates for inspire_list_documents: {e}")

    valid_candidates = [c for c in candidates if c and c not in ('None', '', 'null', 'new')]
    if not valid_candidates:
        return []

    out = insp_model.InspireHandler.list(candidates=valid_candidates, offset=start)
    raw_list = insp_model.table_dictize(out, context) if out else []

    # Deduplicar entradas consecutivas que pertenezcan a la misma operación (diferencia < 5 segundos)
    import datetime
    deduped = []
    seen_times = []
    seen_md5s = set()
    for item in raw_list:
        md5_val = item.get('md5')
        if md5_val in seen_md5s:
            continue
        t_str = item.get('time')
        is_dup = False
        if t_str:
            try:
                clean_t = t_str.rstrip('Z')
                item_dt = datetime.datetime.fromisoformat(clean_t)
                for s_dt in seen_times:
                    if abs((item_dt - s_dt).total_seconds()) < 5:
                        is_dup = True
                        break
                if not is_dup:
                    seen_times.append(item_dt)
            except Exception:
                pass
        if not is_dup:
            seen_md5s.add(md5_val)
            deduped.append(item)
    return deduped

