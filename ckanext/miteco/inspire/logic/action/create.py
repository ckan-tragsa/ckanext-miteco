from ckanext.miteco.inspire import model as insp_model
from ckan.lib.navl.dictization_functions import flatten_dict, unflatten
from ckanext.schemingdcat.lib.csw_mapper.xslt_transformer import XSLTTransformer
from ckanext.dcat.processors import RDFParserException, RDFParser
from ckanext.miteco.lib.rdfParser import mitecoRDFParser
import logging, traceback, tempfile
import ckan.plugins as p
import ckan.lib.helpers as h
from ckan import model
from ckanext.miteco.config import RDF_DATASET_TEMPLATE
from copy import deepcopy
from ckan.logic import NotFound, NotAuthorized
from ckanext.spatial.harvesters import SpatialHarvester
from ckanext.spatial.harvested_metadata import ISODocument
from lxml import etree
if not hasattr(etree, '_ElementStringResult'):
    etree._ElementStringResult = getattr(etree, '_ElementUnicodeResult', str)

log = logging.getLogger(__name__)



def extract_md_metadata(xml_string):
    """
    If xml_string is wrapped in a CSW response (e.g. GetRecordByIdResponse)
    or other envelope, extract the inner gmd:MD_Metadata or gmi:MI_Metadata element.
    Strips UTF-8 BOM if present.
    """
    if not xml_string or not isinstance(xml_string, str):
        return xml_string
    try:
        stripped = xml_string.lstrip('\ufeff').strip()
        if not stripped.startswith('<'):
            return xml_string
        root = etree.fromstring(stripped.encode('utf-8'))
        local_name = etree.QName(root.tag).localname if isinstance(root.tag, str) else ''
        if local_name in ('MD_Metadata', 'MI_Metadata'):
            return stripped

        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            tag_local = etree.QName(elem.tag).localname
            if tag_local in ('MD_Metadata', 'MI_Metadata'):
                return etree.tostring(elem, encoding='utf-8', xml_declaration=True).decode('utf-8')
    except Exception as e:
        log.warning(f"Could not check or extract MD_Metadata from XML: {e}")
    return xml_string.lstrip('\ufeff').strip()


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
    # Authorization
    user = context.get('user')
    if not user:
        raise p.toolkit.NotAuthorized('User must be logged in to add documents')

    uuid = data_dict.get('id')
    xml = data_dict.get('xml')
    xml = extract_md_metadata(xml)
    data_dict['xml'] = xml
    org = data_dict.get('org')
    update = data_dict.get('update')

    if not xml:
        raise p.toolkit.ValidationError({'xml': ['No XML content provided']})

    # Resolver org si no viene provista
    if not org and uuid:
        try:
            pkg_model = model.Package.get(uuid)
            if pkg_model:
                org = pkg_model.owner_org
                data_dict['org'] = org
        except Exception:
            pass
    if not org:
        try:
            u_orgs = p.toolkit.get_action('organization_list_for_user')(context, {})
            if u_orgs:
                org = u_orgs[0].get('name') or u_orgs[0].get('id')
                data_dict['org'] = org
        except Exception:
            pass

    user_obj = model.User.get(user)

    # Hereda los permisos de package_create
    if not user_obj or not p.toolkit.check_access('package_create', context, {"id": uuid, "owner_org": org}):
        raise p.toolkit.NotAuthorized(f'User {user} not authorized')

    # Validación INSPIRE previa a la persistencia
    valid, errors = validate_insp(xml)
    if not valid or errors:
        return {'success': False, 'msg': f'{errors}'}

    # Persistir en base de datos una vez validado y autorizado
    pk = insp_model.setDocument(uuid, xml)

    is_update = p.toolkit.asbool(update)

    if is_update:
        data, fill_errors = xsl_fill(xml)
        if fill_errors and not data:
            return {'success': False, 'msg': f'{fill_errors}'}

        data['spatial_advanced_xml'] = pk
        data['is_spatial_advanced'] = 'true'
        if org:
            data['owner_org'] = org

        target_id = uuid or data.get('id') or data.get('name')
        if target_id:
            data['id'] = target_id
            if 'name' not in data:
                data['name'] = target_id

        pkg_exists = False
        existing_pkg = None
        if target_id:
            try:
                pkg_model = model.Package.get(target_id)
                if pkg_model:
                    pkg_exists = True
                    show_context = {
                        'model': model,
                        'session': model.Session,
                        'user': user,
                        'ignore_auth': True,
                    }
                    existing_pkg = p.toolkit.get_action('package_show')(show_context, {'id': target_id})
            except Exception as e_chk:
                log.warning(f"Error checking existing package {target_id}: {e_chk}")
                pkg_exists = False

        pkg_obj = None
        if pkg_exists:
            if existing_pkg:
                merged_data = deepcopy(existing_pkg)
                for k, v in data.items():
                    if v is not None and v != '':
                        merged_data[k] = v
                merged_data['spatial_advanced_xml'] = pk
                merged_data['is_spatial_advanced'] = 'true'
                if org:
                    merged_data['owner_org'] = org
                for k, v in RDF_DATASET_TEMPLATE.items():
                    if k not in merged_data or merged_data[k] is None or merged_data[k] == '':
                        merged_data[k] = deepcopy(v)
                if not merged_data.get('topic'):
                    merged_data['topic'] = data.get('topic') or 'http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/environment'
                try:
                    pkg_obj = p.toolkit.get_action('package_update')(context, merged_data)
                except Exception as e_up:
                    log.warning(f"package_update failed on merged dict: {e_up}. Trying package_patch...")
                    pkg_obj = p.toolkit.get_action('package_patch')(context, data)
            else:
                pkg_obj = p.toolkit.get_action('package_patch')(context, data)
        else:
            if not data.get('owner_org'):
                if org:
                    data['owner_org'] = org
                else:
                    try:
                        user_orgs = p.toolkit.get_action('organization_list_for_user')(context, {})
                        if user_orgs:
                            data['owner_org'] = user_orgs[0].get('name') or user_orgs[0].get('id')
                    except Exception:
                        pass
                if not data.get('owner_org'):
                    try:
                        all_orgs = p.toolkit.get_action('organization_list')(context, {})
                        if all_orgs:
                            data['owner_org'] = all_orgs[0]
                    except Exception:
                        pass

            for k, v in RDF_DATASET_TEMPLATE.items():
                if k not in data or data[k] is None or data[k] == '':
                    data[k] = deepcopy(v)

            if not data.get('topic'):
                data['topic'] = 'http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/environment'

            if not data.get('title_translated'):
                t_val = data.get('title') or target_id or 'Conjunto de datos espacial'
                data['title_translated'] = {'es': t_val, 'en': t_val}
            if not data.get('title'):
                data['title'] = data.get('title_translated', {}).get('es', 'Conjunto de datos espacial')

            if not data.get('notes_translated'):
                n_val = data.get('notes') or 'Metadatos espaciales importados desde XML INSPIRE'
                data['notes_translated'] = {'es': n_val, 'en': n_val}
            if not data.get('notes'):
                data['notes'] = data.get('notes_translated', {}).get('es', 'Metadatos espaciales importados desde XML INSPIRE')

            if not data.get('name'):
                candidate_name = target_id or data.get('title') or 'inspire-dataset'
                data['name'] = h.slugify(candidate_name)

            pkg_obj = p.toolkit.get_action('package_create')(context, data)
            if isinstance(pkg_obj, dict) and pkg_obj.get('id'):
                try:
                    insp_doc = model.Session.query(insp_model.InspireHandler).filter_by(md5=pk).first()
                    if insp_doc:
                        insp_doc.uuid = pkg_obj['id']
                        model.Session.commit()
                except Exception as e_link:
                    log.warning(f"Could not link inspire_xml {pk} to dataset id: {e_link}")

    else:
        pkg_obj = None
        if uuid:
            d, id_err = p.toolkit.navl_validate({"id": uuid}, {"id": [p.toolkit.get_validator("package_id_exists")]}, context)
            if not id_err:
                pkg_obj = p.toolkit.get_action('package_patch')(context, {'id': uuid, 'spatial_advanced_xml': pk, 'is_spatial_advanced': 'true'})

    pkg_name = ''
    if isinstance(pkg_obj, dict):
        pkg_name = pkg_obj.get('name') or pkg_obj.get('id', '')
    elif target_id or uuid:
        pkg_name = target_id or uuid

    return {'success': True, 'md5': pk, 'package': pkg_name}

try:
    from ckan.logic import auth_audit_exempt
    inspire_push_document = auth_audit_exempt(inspire_push_document)
except ImportError:
    inspire_push_document.auth_audit_exempt = True


"""
Fills the rest of fields of the schema based on the provided xml document
"""
def xsl_fill(xml):
    errors = []
    xml = extract_md_metadata(xml)
    parser = RDFParser()
    profiles = ['miteco_dcat_ap']
    #log.debug('Load profiles TO RDFParser: %s', profiles)
    try:
        parser._profiles = parser._load_profiles(profiles)
    except Exception as e_prof:
        log.warning(f"Error loading RDF profiles {profiles}: {e_prof}")

    parsed_dataset = {}
    try:
        #hacemos la transformación
        transformer = XSLTTransformer("custom-transform.xsl", None)
        transformed_xml = transformer.transform(xml)
        #log.debug(transformed_xml)

        parser.parse(transformed_xml, _format='xml')
        datasets = list(parser.datasets())
        if datasets:
            parsed_dataset = datasets[0]
    except Exception as e:
        errors.append(f'Error parsing the XML file in upload: {e}')
        log.warning(f"Error transforming/parsing XML via XSLT: {e}")

    # Fallback directo al XML con XPath para campos esenciales
    try:
        tree_iso = etree.fromstring(xml.encode('utf-8'))
        is_service = bool(tree_iso.xpath('//*[local-name()="SV_ServiceIdentification"]'))
        if is_service:
            parsed_dataset['dcat_type'] = 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/service'
        else:
            parsed_dataset.setdefault('dcat_type', 'http://inspire.ec.europa.eu/metadata-codelist/ResourceType/dataset')

        # Topic category
        if not parsed_dataset.get('topic'):
            tc_nodes = tree_iso.xpath('//*[local-name()="topicCategory"]/*[local-name()="MD_TopicCategoryCode"]')
            if tc_nodes and tc_nodes[0].text and tc_nodes[0].text.strip():
                tc_code = tc_nodes[0].text.strip()
                parsed_dataset['topic'] = f"http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/{tc_code}"
            else:
                parsed_dataset['topic'] = 'http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/environment'

        # Title
        if not parsed_dataset.get('title') and not parsed_dataset.get('title_translated'):
            t_nodes = tree_iso.xpath('//*[local-name()="citation"]/*[local-name()="CI_Citation"]/*[local-name()="title"]/*[local-name()="CharacterString"]')
            if t_nodes and t_nodes[0].text and t_nodes[0].text.strip():
                t_val = t_nodes[0].text.strip()
                parsed_dataset['title'] = t_val
                parsed_dataset['title_translated'] = {'es': t_val, 'en': t_val}

        # Abstract / Notes
        if not parsed_dataset.get('notes') and not parsed_dataset.get('notes_translated'):
            a_nodes = tree_iso.xpath('//*[local-name()="abstract"]/*[local-name()="CharacterString"]')
            if a_nodes and a_nodes[0].text and a_nodes[0].text.strip():
                a_val = a_nodes[0].text.strip()
                parsed_dataset['notes'] = a_val
                parsed_dataset['notes_translated'] = {'es': a_val, 'en': a_val}

        # Identifier
        if not parsed_dataset.get('id') and not parsed_dataset.get('name'):
            f_nodes = tree_iso.xpath('//*[local-name()="fileIdentifier"]/*[local-name()="CharacterString"]')
            if f_nodes and f_nodes[0].text and f_nodes[0].text.strip():
                fid = f_nodes[0].text.strip()
                parsed_dataset['id'] = fid
                parsed_dataset['name'] = fid
    except Exception as e_xp:
        log.warning(f"Error in direct XML extraction: {e_xp}")

    parsed_dataset['is_spatial_advanced'] = 'true'
    return (parsed_dataset, errors)


def validate_insp(xml_string):
    """
    Validate inspire xml without transforming it to RDF.
    Supports both dataset metadata (gmx.xsd) and spatial services (gmx_and_srv.xsd).
    """
    if not xml_string or not isinstance(xml_string, str):
        return False, ['Empty or invalid XML string']

    xml_string = extract_md_metadata(xml_string)

    try:
        encoded_xml = xml_string.encode("utf-8")
        xml = etree.fromstring(encoded_xml)

        # Check if the metadata record is a Service Identification (e.g. WMS, WFS, CSW)
        is_service = bool(xml.xpath('//*[local-name()="SV_ServiceIdentification"]'))

        if is_service:
            import os
            import ckanext.spatial.validation as val_module
            from ckanext.spatial.validation.validation import ISO19139EdenSchema
            xsd_dir = os.path.dirname(val_module.__file__)
            gmx_and_srv_xsd = os.path.join(xsd_dir, 'xml/iso19139eden/gmx_and_srv.xsd')
            is_valid, errors = ISO19139EdenSchema._is_valid(xml, gmx_and_srv_xsd, 'Service schema (gmx_and_srv.xsd)')
            return is_valid, errors

        from ckanext.spatial.validation.validation import Validators
        # Use iso19139eden for full INSPIRE compliance
        validators = Validators(profiles=['iso19139eden'])
        valid, schema, errors = validators.is_valid(xml)
        if valid or not errors:
            return True, []

        return valid, errors
    except etree.XMLSyntaxError as e:
        return False, [f'Invalid XML syntax: {e}']
    except Exception as e:
        log.exception(f'Error validating inspire XML: {e}')
        return False, [str(e)]