import json
import logging
import datetime
from typing import Dict, Any, Tuple, List, Optional
from lxml import etree

from ckan import model
import ckan.plugins.toolkit as toolkit
from ckanext.miteco.inspire import model as insp_model
from ckanext.miteco.inspire.logic.action.create import validate_insp, extract_md_metadata
from ckanext.miteco.config import OGC2CKAN_HARVESTER_MD_CONFIG

log = logging.getLogger(__name__)

# BBOX oficial de España por defecto para metadatos espaciales nacionales
DEFAULT_SPAIN_BBOX = [-18.16, 27.64, 4.32, 43.79]

TOPIC_CODE_LIST = [
    'farming', 'biota', 'boundaries', 'climatologyMeteorologyAtmosphere',
    'economy', 'elevation', 'environment', 'geoscientificInformation',
    'health', 'imageryBaseMapsEarthCover', 'intelligenceMilitary',
    'inlandWaters', 'location', 'oceans', 'planningCadastre',
    'society', 'structure', 'transportation', 'utilitiesCommunication'
]


def _extract_bbox_from_geojson(geojson_raw: Any) -> Optional[List[float]]:
    """
    Extracts [west, south, east, north] bounding box from a GeoJSON polygon string or dict.
    """
    if not geojson_raw:
        return None
    try:
        data = geojson_raw if isinstance(geojson_raw, dict) else json.loads(geojson_raw)
        coords = []
        geom_type = data.get('type')
        if geom_type == 'Polygon':
            for ring in data.get('coordinates', []):
                coords.extend(ring)
        elif geom_type == 'MultiPolygon':
            for poly in data.get('coordinates', []):
                for ring in poly:
                    coords.extend(ring)
        elif geom_type == 'Point':
            pt = data.get('coordinates', [])
            if len(pt) >= 2:
                return [float(pt[0]), float(pt[1]), float(pt[0]), float(pt[1])]

        if coords:
            xs = [float(c[0]) for c in coords if len(c) >= 2]
            ys = [float(c[1]) for c in coords if len(c) >= 2]
            if xs and ys:
                return [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)]
    except Exception as e:
        log.debug(f"Error parsing spatial GeoJSON: {e}")
    return None


def _clean_topic_category(topic_val: Any) -> str:
    """
    Normalizes a topicCategory string or URI to a valid ISO 19139 MD_TopicCategoryCode.
    """
    if not topic_val:
        return 'environment'
    val_str = str(topic_val).strip().rstrip('/')
    code = val_str.split('/')[-1]
    for valid_code in TOPIC_CODE_LIST:
        if valid_code.lower() == code.lower():
            return valid_code
    return 'environment'


def build_inspire_record(pkg_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a CKAN package dictionary (following MITECO schemingdcat schema)
    to a structured dictionary matching the ISO 19139 INSPIRE Jinja2 templates.
    """
    pkg_id = pkg_dict.get('id') or pkg_dict.get('name') or 'dataset-inspire-template'
    title = (
        pkg_dict.get('title')
        or (pkg_dict.get('title_translated') or {}).get('es')
        or pkg_dict.get('name')
        or 'Conjunto de datos'
    )
    abstract = (
        pkg_dict.get('notes')
        or (pkg_dict.get('notes_translated') or {}).get('es')
        or 'Sin descripción disponible'
    )

    # Detección de fecha de metadato
    today_str = datetime.date.today().isoformat()
    datestamp = today_str
    if pkg_dict.get('metadata_modified'):
        datestamp = str(pkg_dict['metadata_modified']).split('T')[0]

    # Fechas de citación
    dates = []
    created_date = (
        pkg_dict.get('created')
        or pkg_dict.get('metadata_created')
        or today_str
    )
    dates.append({
        'date': str(created_date).split('T')[0],
        'type': 'creation'
    })
    if pkg_dict.get('miteco_publication_date'):
        pub_date = str(pkg_dict['miteco_publication_date']).split('T')[0]
        dates.append({
            'date': pub_date,
            'type': 'publication'
        })

    # Detección de recurso (Dataset vs Servicio espacial)
    dcat_type = str(pkg_dict.get('dcat_type') or '').lower()
    is_service = ('service' in dcat_type) or (pkg_dict.get('type') == 'service')
    resource_type = 'service' if is_service else 'dataset'

    # Contacto / Responsable
    org_name = (
        pkg_dict.get('publisher_name')
        or pkg_dict.get('contact_name')
        or pkg_dict.get('author_name')
        or (pkg_dict.get('organization') or {}).get('title')
        or OGC2CKAN_HARVESTER_MD_CONFIG.get('publisher_name')
        or 'Ministerio para la Transición Ecológica y el Reto Demográfico'
    )
    email = (
        pkg_dict.get('contact_email')
        or pkg_dict.get('publisher_email')
        or pkg_dict.get('author_email')
        or OGC2CKAN_HARVESTER_MD_CONFIG.get('publisher_email')
        or 'bzn-datos@miteco.es'
    )
    contact_url = (
        pkg_dict.get('contact_url')
        or pkg_dict.get('publisher_url')
        or OGC2CKAN_HARVESTER_MD_CONFIG.get('publisher_url')
        or 'https://www.miteco.gob.es/'
    )

    contacts = {
        'pointOfContact': {
            'organization': org_name,
            'email': email,
            'url': contact_url,
            'country': 'España'
        }
    }

    # Palabras clave
    kw_list = []
    for tag in pkg_dict.get('tags', []):
        t_name = tag.get('name') if isinstance(tag, dict) else str(tag)
        if t_name and t_name.strip():
            kw_list.append(t_name.strip())

    keywords_blocks = []
    if kw_list:
        keywords_blocks.append({
            'keywords': kw_list,
            'thesaurus_title': None,
            'thesaurus_uri': None
        })

    # Tema GEMET INSPIRE
    topic_clean = _clean_topic_category(pkg_dict.get('topic'))
    keywords_blocks.append({
        'keywords': [{'name': topic_clean, 'uri': f'http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/{topic_clean}'}],
        'thesaurus_title': 'GEMET - INSPIRE themes, version 1.0',
        'thesaurus_uri': 'http://inspire.ec.europa.eu/theme',
        'thesaurus_date': '2008-06-01'
    })

    # Cobertura espacial (BBOX)
    bbox = _extract_bbox_from_geojson(pkg_dict.get('spatial'))
    if not bbox:
        bbox = DEFAULT_SPAIN_BBOX

    # Distribuciones / Recursos
    distributions = {}
    for idx, res in enumerate(pkg_dict.get('resources', [])):
        r_url = res.get('url')
        if not r_url:
            continue
        r_name = res.get('name') or f"Recurso {idx + 1}"
        r_format = res.get('format') or 'Desconocido'
        distributions[f"resource_{idx}"] = {
            'name': r_name,
            'url': r_url,
            'format': r_format,
            'format_uri': None,
            'format_version': None,
            'type': 'WWW:LINK',
            'description': res.get('description') or '',
            'function': 'download' if not is_service else 'information'
        }

    # Linaje / Calidad
    miteco_meth = pkg_dict.get('miteco_meth')
    miteco_meth_str = None
    if isinstance(miteco_meth, list):
        items = [str(x).strip() for x in miteco_meth if x and str(x).strip()]
        if items:
            miteco_meth_str = ", ".join(items)
    elif isinstance(miteco_meth, str) and miteco_meth.strip() not in ('', '[]', "['']", 'None'):
        miteco_meth_str = miteco_meth.strip()

    lineage_stmt = (
        pkg_dict.get('lineage_process_steps')
        or pkg_dict.get('provenance')
        or miteco_meth_str
        or OGC2CKAN_HARVESTER_MD_CONFIG.get('lineage_process_steps')
        or 'Datos generados y mantenidos por el Ministerio para la Transición Ecológica y el Reto Demográfico.'
    )

    record = {
        'metadata': {
            'identifier': pkg_id,
            'language': 'spa',
            'charset': 'utf8',
            'datestamp': datestamp,
            'hierarchylevel': {'value': resource_type}
        },
        'identification': {
            'title': title,
            'abstract': abstract,
            'dates': dates,
            'identifier': pkg_dict.get('miteco_identifier') or pkg_dict.get('inspire_id') or pkg_id,
            'keywords': keywords_blocks,
            'topiccategory': [topic_clean],
            'license_title': pkg_dict.get('license_title') or 'Creative Commons Attribution 4.0 (CC-BY 4.0)',
            'access_rights': pkg_dict.get('access_rights') or 'http://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess/noLimitations',
            'language': 'spa',
            'service_type': 'OGC:WMS' if is_service else None,
            'service_type_version': '1.3.0' if is_service else None
        },
        'contact': contacts,
        'spatial': {
            'crs': {'value': '4258', 'uri': 'http://www.opengis.net/def/crs/EPSG/0/4258'},
            'bbox': bbox,
            'spatialresolution': pkg_dict.get('spatial_resolution_in_meters')
        },
        'distribution': distributions,
        'dataquality': {
            'lineage': {
                'statement': lineage_stmt
            }
        }
    }
    return record


def render_inspire_xml(pkg_dict: Dict[str, Any]) -> str:
    """
    Renders the ISO 19139 INSPIRE XML string from a package dictionary
    using the Jinja2 templates in ckanext-miteco.
    """
    record = build_inspire_record(pkg_dict)
    raw_xml = toolkit.render('inspire/generator/main.j2', extra_vars={'record': record})

    # Pretty print y formateo canónico con lxml
    try:
        parser = etree.XMLParser(remove_blank_text=True, encoding='utf-8')
        root = etree.fromstring(raw_xml.encode('utf-8'), parser)
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')
    except Exception as e:
        log.warning(f"Error pretty-printing generated XML: {e}")
        return raw_xml


def generate_inspire_xml(
    pkg_dict: Dict[str, Any],
    persist: bool = False,
    user: Optional[str] = None
) -> Tuple[bool, str, List[str]]:
    """
    Generates and optionally persists an official INSPIRE ISO 19139 XML for a dataset or service.

    Behavior:
    1. If the dataset already has a manually uploaded XML (is_spatial_advanced is true and
       spatial_advanced_xml is set), it respects it and does not overwrite it.
    2. Renders the XML using the official ISO 19139 INSPIRE templates.
    3. Validates the generated XML against validate_insp (supporting datasets & spatial services).
    4. If persist=True and valid, stores it in inspire_xml_table and returns the stored document key.

    Returns:
        (success: bool, result_or_xml: str, errors: list)
    """
    if not pkg_dict:
        return False, "", ["No package dictionary provided"]

    # 1. Respetar XML existente subido por el usuario
    if toolkit.asbool(pkg_dict.get('is_spatial_advanced')) and pkg_dict.get('spatial_advanced_xml'):
        from ckanext.miteco.inspire.access import find_document
        existing_doc = find_document(pkg_dict)
        if existing_doc and existing_doc.xml:
            log.info(f"Package {pkg_dict.get('name')} already has user XML. Preserving existing document.")
            return True, existing_doc.xml, []

    # 2. Renderizar XML
    try:
        xml_string = render_inspire_xml(pkg_dict)
    except Exception as e:
        log.exception(f"Error rendering inspire XML: {e}")
        return False, "", [f"Template rendering error: {e}"]

    # 3. Validar contra el validador oficial INSPIRE
    is_valid, errors = validate_insp(xml_string)
    if not is_valid or errors:
        log.warning(f"Generated XML for {pkg_dict.get('name')} failed validation: {errors}")
        return False, xml_string, errors

    # 4. Persistir en la base de datos si se solicita
    if persist:
        pkg_id = pkg_dict.get('id') or pkg_dict.get('name')
        try:
            pk = insp_model.setDocument(pkg_id, xml_string)
            return True, pk, []
        except Exception as e:
            log.exception(f"Error persisting generated inspire XML for {pkg_id}: {e}")
            return False, xml_string, [f"Persistence error: {e}"]

    return True, xml_string, []


def sync_xml_with_package(xml_content, pkg_dict):
    """
    Synchronizes an existing ISO 19139 / INSPIRE XML string with the latest metadata
    stored in the CKAN package dictionary (title, description/abstract, dateStamp,
    identifier, etc.), preserving all spatial and structural XML tags.
    """
    if not xml_content or not isinstance(xml_content, str) or not xml_content.strip().startswith('<'):
        return xml_content
    if not pkg_dict or not isinstance(pkg_dict, dict):
        return xml_content

    try:
        from lxml import etree
        import datetime
        root = etree.fromstring(xml_content.encode('utf-8'))

        ns = {
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'gco': 'http://www.isotc211.org/2005/gco',
            'srv': 'http://www.isotc211.org/2005/srv',
            'gmx': 'http://www.isotc211.org/2005/gmx',
        }

        changed = False

        # 1. Title
        title_val = pkg_dict.get('title')
        if not title_val and isinstance(pkg_dict.get('title_translated'), dict):
            title_val = pkg_dict['title_translated'].get('es') or pkg_dict['title_translated'].get('en')
        if title_val and str(title_val).strip():
            title_nodes = root.xpath('//gmd:identificationInfo/*/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString', namespaces=ns)
            for node in title_nodes:
                if node.text != str(title_val).strip():
                    node.text = str(title_val).strip()
                    changed = True

        # 2. Abstract / Notes
        notes_val = pkg_dict.get('notes')
        if not notes_val and isinstance(pkg_dict.get('notes_translated'), dict):
            notes_val = pkg_dict['notes_translated'].get('es') or pkg_dict['notes_translated'].get('en')
        if notes_val and str(notes_val).strip():
            abstract_nodes = root.xpath('//gmd:identificationInfo/*/gmd:abstract/gco:CharacterString', namespaces=ns)
            for node in abstract_nodes:
                if node.text != str(notes_val).strip():
                    node.text = str(notes_val).strip()
                    changed = True

        # 4. Identifier / code
        identifier_val = (
            pkg_dict.get('miteco_identifier') or
            pkg_dict.get('identifier') or
            pkg_dict.get('inspire_id')
        )
        if identifier_val and str(identifier_val).strip():
            id_nodes = root.xpath('//gmd:identificationInfo/*/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString', namespaces=ns)
            for node in id_nodes:
                if node.text != str(identifier_val).strip():
                    node.text = str(identifier_val).strip()
                    changed = True

        if not changed:
            return xml_content
        now = datetime.datetime.now(datetime.timezone.utc)
        for node in root.xpath('//gmd:dateStamp/gco:Date | //gmd:dateStamp/gco:DateTime', namespaces=ns):
            node.text = now.date().isoformat() if etree.QName(node).localname == 'Date' else now.isoformat().replace('+00:00', 'Z')
        synced = etree.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
        valid, errors = validate_insp(synced)
        if not valid or errors:
            log.warning('Synchronized INSPIRE XML failed validation; preserving stored XML')
            return xml_content
        return synced
    except Exception as e:
        log.warning(f"Could not synchronize XML with package metadata: {e}")
        return xml_content
