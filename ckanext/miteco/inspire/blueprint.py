from logging import getLogger
from flask import Blueprint, request, jsonify  # type: ignore
from ckan import model  # type: ignore
import ckan.plugins.toolkit as toolkit  # type: ignore

log = getLogger(__name__)

inspire = Blueprint(u'inspire', __name__,
                    url_prefix=u'/inspire')

@inspire.route(u'/dataset/new', defaults={'id': ''})
@inspire.route(u'/dataset/<id>')
def inspire_form(id):
    log.debug(id)
    package = {}
    if id:
        context = {
            'model': model,
            'session': model.Session,
            'ignore_auth': True,
        }
        try:
            package = toolkit.get_action("package_show")(context, {"id": id})
        except Exception as e:
            log.exception(f"Error loading package {id}: {e}")

    return toolkit.render('miteco/inspire.html', extra_vars={
        u'pkg_dict': package,
        u'data': package,
        u'form_vars': {u'field': {u'field_name': "spatial_advanced_xml"}},
        u'form_snippet': u'schemingdcat/form_snippets/inspire_xml.html',
        u'is_inspire_form': True,
    })


@inspire.route(u'/dataset/upload-xml', defaults={'id': ''}, methods=['POST'])
@inspire.route(u'/dataset/<id>/upload-xml', methods=['POST'])
def inspire_upload_xml(id):
    """
    Internal endpoint to process and import an INSPIRE XML file.
    Executes inspire_push_document with update=True using the current session.
    """
    user = getattr(toolkit.c, 'user', None) or getattr(toolkit.g, 'user', None)
    if not user:
        return jsonify({'success': False, 'msg': toolkit._('User must be logged in to import XML')}), 401

    xml_content = None
    if 'file' in request.files:
        uploaded_file = request.files['file']
        xml_content = uploaded_file.read().decode('utf-8', errors='replace')
        if not id and hasattr(request, 'form'):
            id = request.form.get('id', '')
    elif request.is_json:
        json_data = request.get_json() or {}
        xml_content = json_data.get('xml')
        if not id:
            id = json_data.get('id', '')
    else:
        xml_content = request.form.get('xml') if hasattr(request, 'form') else None
        if not id and hasattr(request, 'form'):
            id = request.form.get('id', '')

    if id in ('new', 'None', None):
        id = ''

    if not xml_content or not xml_content.strip():
        return jsonify({'success': False, 'msg': toolkit._('No XML content provided')}), 400

    from ckanext.miteco.inspire.logic.action.create import extract_md_metadata
    xml_content = extract_md_metadata(xml_content)

    # Si es un dataset nuevo y no tiene id, intentar extraer fileIdentifier del XML
    if not id:
        try:
            from lxml import etree
            tree = etree.fromstring(xml_content.encode('utf-8'))
            namespaces = {'gmd': 'http://www.isotc211.org/2005/gmd', 'gco': 'http://www.isotc211.org/2005/gco'}
            fid_el = tree.xpath('//gmd:fileIdentifier/gco:CharacterString', namespaces=namespaces)
            if fid_el and fid_el[0].text and fid_el[0].text.strip():
                id = fid_el[0].text.strip()
        except Exception:
            pass

    context = {
        'model': model,
        'session': model.Session,
        'user': user,
        'auth_user_obj': getattr(toolkit.c, 'userobj', None) or getattr(toolkit.g, 'userobj', None),
    }

    org = None
    if hasattr(request, 'form') and request.form.get('org'):
        org = request.form.get('org')
    elif request.is_json and request.get_json():
        org = request.get_json().get('org')

    if id:
        try:
            pkg_model = model.Package.get(id)
            if pkg_model and not org:
                org = pkg_model.owner_org
        except Exception as e_pkg:
            log.debug(f"Error checking package {id} in model: {e_pkg}")

    if not org:
        try:
            user_orgs = toolkit.get_action('organization_list_for_user')(context, {})
            if user_orgs:
                org = user_orgs[0].get('name') or user_orgs[0].get('id')
        except Exception:
            pass

    if not org:
        try:
            all_orgs = toolkit.get_action('organization_list')(context, {})
            if all_orgs:
                org = all_orgs[0]
        except Exception:
            pass

    overwrite = True
    if hasattr(request, 'form') and 'overwrite' in request.form:
        overwrite = toolkit.asbool(request.form.get('overwrite'))
    elif request.is_json and request.get_json() and 'overwrite' in request.get_json():
        overwrite = toolkit.asbool(request.get_json().get('overwrite'))

    data_dict = {
        'id': id or None,
        'xml': xml_content,
        'org': org,
        'update': True,
        'overwrite': overwrite
    }


    try:
        result = toolkit.get_action('inspire_push_document')(context, data_dict)
        return jsonify(result)
    except toolkit.NotAuthorized as e:
        return jsonify({'success': False, 'msg': str(e)}), 403
    except toolkit.ValidationError as e:
        return jsonify({'success': False, 'msg': str(e.error_dict or e)}), 400
    except Exception as e:
        log.exception(f"Error importing inspire XML for {id}: {e}")
        return jsonify({'success': False, 'msg': str(e)}), 500

