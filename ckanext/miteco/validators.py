import logging
import uuid
import datetime
from urllib.parse import urlparse
from ckan.lib.navl.dictization_functions import flatten_dict, unflatten
from ckanext.dcat.processors import RDFParserException, RDFParser

import ckan.plugins as p
from ckan.common import _
from ckantoolkit import missing

from ckanext.schemingdcat.utils import _load_yaml
from ckanext.schemingdcat.lib.csw_mapper.xslt_transformer import XSLTTransformer
from ckanext.dcat.processors import RDFParserException, RDFParser
from ckanext.miteco.lib.rdfParser import mitecoRDFParser


from ckanext.schemingdcat.config import (
    INSPIRE_HVD_CATEGORY,
    DCAT_AP_HVD_CATEGORY_LEGISLATION
)
import ckanext.miteco.helpers as miteco_helpers
from ckanext.miteco.config import (
    MITECO_DEFAULT_HVD_CATEGORY,   
    MITECO_DEFAULT_GENERAL_TYPE_HVDS,
    MITECO_INSPIRE_GENERAL_TYPE,
    miteco_rdf_parser
    
)


from ckan.lib.navl.dictization_functions import Missing

log = logging.getLogger(__name__)

all_validators = {}

FORM_EXTRAS = ('__extras',)

DEFAULT_RDF_PROFILES = ['eu_geodcat_ap_3']
DEBUG_MODE = p.toolkit.asbool(p.toolkit.config.get('debug', False))

def validator(fn):
    """
    collect validator functions into ckanext.schemingdcat.all_validators dict
    """
    all_validators[fn.__name__] = fn
    return fn

def scheming_validator(fn):
    """
    Decorate a validator that needs to have the scheming fields
    passed with this function. When generating navl validator lists
    the function decorated will be called passing the field
    and complete schema to produce the actual validator for each field.
    """
    fn.is_a_scheming_validator = True
    return fn

@scheming_validator
@validator
def miteco_internal_identifier(field, schema):
    """
    Generates an identifier based on the values of hvd_category and theme_es, and assigns a numeric value of xx digits.
    
    Args:
    - value: A string representing the value.
    
    Returns:
    - The generated identifier string.
    """
    
    miteco_identifier_schema = _load_yaml(p.toolkit.config.get('ckanext.miteco.miteco_identifier_schema'))
    
    def validator(key, data, errors, context):        
        # Check if the identifier already exists
        existing_identifier = data.get(('miteco_identifier', ))
        if existing_identifier:
            ##log.debug('Existing identifier found: %s', existing_identifier)
            return
        
        hvd_category = data.get(('hvd_category', ))
        theme_es = data.get(('theme_es', ))
        dataset_scope = data.get(('dataset_scope', ))
        ##log.debug('hvd_category: %s, theme_es: %s and dataset_scope: %s', hvd_category, theme_es, dataset_scope)
        
        # Tipo de dato
        tipo_dato = next((item['miteco_id_code'] for item in miteco_identifier_schema['miteco_id_tipo-dato'] if item['id'] == 'hvd_category'), '00')
        
        # Área y Subárea
        if hvd_category:
            area_subarea = next((item for item in miteco_identifier_schema['miteco_id_area-subarea'] if item['id'] == hvd_category), None)
            if not area_subarea:
                area_subarea = next((item for item in miteco_identifier_schema['miteco_id_area-subarea'] if item['id'] == 'non_hvd_category'), None)
            if not area_subarea:
                area_subarea = next((item for item in miteco_identifier_schema['miteco_id_area-subarea'] if item['id'] == 'default'), None)
            
            if area_subarea:
                area = next((item['miteco_id_code'] for item in miteco_identifier_schema['miteco_id_area-subarea'] if item['id'] == area_subarea['area']), '00') if area_subarea['area'] else area_subarea['miteco_id_code']
                subarea = area_subarea['miteco_id_code'] if area_subarea['area'] else '00'
            else:
                area = '00'
                subarea = '00'
        else:
            area = next((item['miteco_id_code'] for item in miteco_identifier_schema['miteco_id_area-subarea'] if item['id'] == theme_es), '00')
            subarea = '00'
        
        # Categoría
        categoria = next((item['miteco_id_code'] for item in miteco_identifier_schema['miteco_id_categoria'] if item['id'] == dataset_scope), '0')
        
        # Conjunto de datos
        dataset_code = 1
        prefix = ''
        
        # Create the identifier
        identifier = f"{str(tipo_dato).zfill(1)}-{str(area).zfill(2)}-{str(categoria).zfill(1)}-{str(subarea).zfill(2)}-{prefix}{str(dataset_code).zfill(4)}"
        
        # Check if identifier already exists and generate a sequential value if necessary
        while miteco_helpers.miteco_check_miteco_identifier(identifier):
            dataset_code += 1
            if dataset_code > 9999:
                dataset_code = 1
                if prefix == '':
                    prefix = 'A'
                else:
                    prefix = chr(ord(prefix) + 1)
                    if prefix > 'Z':
                        errors[key].append("No more identifiers available.")
                        return
            
            identifier = f"{str(tipo_dato).zfill(1)}-{str(area).zfill(2)}-{str(categoria).zfill(1)}-{str(subarea).zfill(2)}-{prefix}{str(dataset_code).zfill(4)}"
        
        ##log.debug('miteco_identifier: %s', identifier)
        
        # Assign the identifier to the key
        data[key] = identifier
    
    return validator

@scheming_validator
@validator
def miteco_uuid_identifier(field, schema):
    """
    Checks if 'id' exists in the data. If not, generates a UUID4 and assigns it to 'id', 'identifier', and 'name'.
    Also ensures that 'id', 'identifier', and 'name' have the same value.

    Args:
        field (dict): Information about the field to be updated.
        schema (dict): The schema for the field to be updated.

    Returns:
        function: A validation function that can be used to update the field based on the presence of 'id'.
    """
    def validator(key, data, errors, context):
        id_key = key[:-1] + ('id',)
        identifier_key = key[:-1] + ('identifier',)
        name_key = key[:-1] + ('name',)

        id_value = data.get(id_key)
        identifier_value = data.get(identifier_key)
        name_value = data.get(name_key)

        if not id_value:
            new_uuid = str(uuid.uuid4())
            data[id_key] = new_uuid
            data[identifier_key] = new_uuid
            data[name_key] = new_uuid
        else:
            if id_value != identifier_value or id_value != name_value:
                data[identifier_key] = id_value
                data[name_key] = id_value
        #log.debug(data)
    return validator

@scheming_validator
@validator
def miteco_miteco_dataset_type_hvd_dataset(field, schema):
    """Validator for MITECO general type HVD dataset.

    This validator checks the `miteco_dataset_type` field and sets the 
    `hvd_category` field accordingly. If `miteco_dataset_type` is in 
    MITECO_DEFAULT_GENERAL_TYPE_HVDS:
    - If it's 'http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL', 
      sets `hvd_category` to `INSPIRE_HVD_CATEGORY`
    - Otherwise, sets `hvd_category` to `MITECO_DEFAULT_HVD_CATEGORY`
    
    For datasets not in MITECO_DEFAULT_GENERAL_TYPE_HVDS, leaves hvd_category untouched.

    When a category is assigned, ensures that `DCAT_AP_HVD_CATEGORY_LEGISLATION` is 
    included in the `applicable_legislation_key` list.

    Args:
        field (str): The field name being validated.
        schema (dict): The schema definition.

    Returns:
        function: The validator function.
    """
    def validator(key, data, errors, context):
        hvd_category = data.get(key)
        #log.debug("key: %s",key)
        #log.debug("Texto de algún tipo = %s", data)
        miteco_dataset_type = data.get(('miteco_dataset_type', ))
        
        hvd = "hvd"
        
        # Only set hvd_category if dataset type is in the HVD list
        if miteco_dataset_type in MITECO_DEFAULT_GENERAL_TYPE_HVDS:        
            if miteco_dataset_type == MITECO_INSPIRE_GENERAL_TYPE:
                data[key] = INSPIRE_HVD_CATEGORY
            else:
                data[key] = MITECO_DEFAULT_HVD_CATEGORY
            
            # Now that we've set an HVD category, ensure the legislation is also set
            applicable_legislation_key = ('applicable_legislation_key', )
            
            if isinstance(data.get(applicable_legislation_key), list):
                if DCAT_AP_HVD_CATEGORY_LEGISLATION not in data[applicable_legislation_key]:
                    data[applicable_legislation_key].append(DCAT_AP_HVD_CATEGORY_LEGISLATION)
            else:
                if data.get(applicable_legislation_key) != DCAT_AP_HVD_CATEGORY_LEGISLATION:
                    data[applicable_legislation_key] = [DCAT_AP_HVD_CATEGORY_LEGISLATION]
        # If not an HVD dataset type and hvd_category is empty, leave it as None
        # (no action needed as we're not modifying data[key])
        claves = [data.get(('hvd_category', ))]
        if all(not isinstance(x, Missing) for x in claves):
            for a, value in data.items():
                if value == 'hvd' and len(a) == 3:
                    num_hvd = a[1]
                    data['extras', num_hvd, 'value'] = "hvd"
        else:
            for a, value in data.items():
                if value == 'hvd' and len(a) == 3:
                    num_hvd = a[1]
                    data['extras', num_hvd, 'value'] = "non_hvd"
    return validator

@scheming_validator
@validator
def miteco_miteco_contact_point(field, schema):
    pass

@scheming_validator
@validator
def miteco_miteco_dataset_ogc_normalize(field, schema):
    """
    Validator to detect OGC services and rewrite the URL to point towards GetCapabilities request
    """
    def validator(key, data, errors, context):
        if data[(key[0],key[1],'format')]:
            format = data[(key[0],key[1],'format')].upper()
            if format in ["WMS","WFS","WMTS","WCS","WPS"]:
                url = urlparse(data[key])
                data[key] = url.scheme+"://"+url.netloc+url.path+"?request=GetCapabilities&service="+format
        
    return validator

@scheming_validator
@validator
def miteco_preserve_date_modified(field, schema):
    """
    Preserves the existing modified date if available.
    Only sets datetime.now() if the field is empty or missing.
    """
    def validator(key, data, errors, context):
        value = data[key]
        if value is missing or value is None or value == '':
            data[key] = datetime.datetime.now().isoformat()
    return validator

@scheming_validator
@validator
def miteco_xsl_fill(field, schema):
    """
    Fills the rest of fields of the schema based on the provided xml document
    """
    def validator(key, data, errors, context):
        log.debug("Filling dataset fields")
        if True:
        #if data['is_spatial_advanced'] != "True":
            parser = RDFParser()
            profiles = ['miteco_dcat_ap']
            log.debug('Load profiles TO RDFParser: %s', profiles)
            parser._profiles = parser._load_profiles(profiles)

            #hacemos la transformación
            transformer = XSLTTransformer("semiceu.xsl", None)
            transformed_xml = transformer.transform(data[('spatial_advanced_xml',)])
            #log.debug(transformed_xml)
            try:
                parser.parse(transformed_xml, _format='xml')            
                parsed_dataset = list(parser.datasets())[0]
            except Exception as e:
                errors[key].append(f'Error parsing the RDF file in upload: {e}')
                return None

            data_unflattened = unflatten(data)
            for extra in parsed_dataset.pop('extras',[]):
                if 'extras' in data_unflattened:
                    for index in range(0,len(data_unflattened['extras'])):
                        if data_unflattened['extras'][index]['key'] == extra['key']:
                            data_unflattened['extras'][index]['value'] = extra['value']
                            break
                    else:
                        data_unflattened['extras'].append(extra)
                else:
                    data_unflattened['extras'] = [extra]
            data = flatten_dict(data_unflattened)
            
            flat_dataset = flatten_dict(parsed_dataset)
            for k in list(flat_dataset.keys()):
                if not flat_dataset[k]:
                    flat_dataset.pop(k,None)
                data.update(flat_dataset)        
            data[('name',)] = data[('title',)]



            
            for kextra, kdict in (
                ('notes_translated-es', [('notes_translated',),'es']),
                ('notes_translated-en', [('notes_translated',),'en']),
                ('title_translated-es', [('title_translated',),'es']),
                ('title_translated-en', [('title_translated',),'en']),
                ('tags', ('tags',)),
                ('pkg_name', ('id',))
                ):
                if isinstance(kdict,list):
                    data[('__extras',)][kextra] = data[kdict[0]][kdict[1]]
                else:
                    data[('__extras',)][kextra] = data[kdict]


        #log.debug(data[('topic',)])
        

    return validator
 
@scheming_validator
@validator
def miteco_iso_validator(field, schema):
    """
    Validates the ISO 19139 XML and persists it to the inspire_xml table for versioning.
    The full XML is kept in the dataset field so the form can reload it correctly.
    """
    def validator(key, data, errors, context):
        from ckantoolkit import missing as tk_missing
        from lxml import etree
        from ckanext.miteco.inspire import model as insp_model

        xml_content = data.get(key)
        if xml_content is tk_missing or not xml_content or not xml_content.strip():
            return

        # Validate well-formed XML
        try:
            etree.fromstring(xml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            errors[key].append(_('Invalid XML: %s') % str(e))
            return

        # Retrieve the dataset UUID (available on update, not on create before first save)
        dataset_id = data.get(('id',))
        if not dataset_id or dataset_id is tk_missing:
            log.debug('miteco_iso_validator: no dataset id yet, skipping inspire_xml persistence')
            return

        # Persist the XML document to the versioned inspire_xml table
        try:
            insp_model.setDocument(str(dataset_id), xml_content)
            log.debug('miteco_iso_validator: XML persisted for dataset %s', dataset_id)
        except Exception as e:
            log.error('miteco_iso_validator: error persisting XML for dataset %s: %s', dataset_id, e)

    return validator

@scheming_validator
@validator
def miteco_boolean(field, schema):
    """
    Checks if the field is "True" or "False"
    """
    def validator(key, data, errors, context):
        pass
            
    return validator
