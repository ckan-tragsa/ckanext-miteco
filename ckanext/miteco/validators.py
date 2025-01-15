import logging
import uuid

import ckan.plugins as p
from ckan.common import _

from ckanext.schemingdcat.utils import _load_yaml

from ckanext.schemingdcat.config import (
    INSPIRE_HVD_CATEGORY,
    DCAT_AP_HVD_CATEGORY_LEGISLATION
)
import ckanext.miteco.helpers as miteco_helpers
from ckanext.miteco.config import (
    MITECO_DEFAULT_HVD_CATEGORY,   
    MITECO_DEFAULT_GENERAL_TYPE_HVDS,
    MITECO_INSPIRE_GENERAL_TYPE
    
)

log = logging.getLogger(__name__)

all_validators = {}

FORM_EXTRAS = ('__extras',)

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
            #log.debug('Existing identifier found: %s', existing_identifier)
            return
        
        hvd_category = data.get(('hvd_category', ))
        theme_es = data.get(('theme_es', ))
        dataset_scope = data.get(('dataset_scope', ))
        #log.debug('hvd_category: %s, theme_es: %s and dataset_scope: %s', hvd_category, theme_es, dataset_scope)
        
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
        
        #log.debug('miteco_identifier: %s', identifier)
        
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

    return validator

@scheming_validator
@validator
def miteco_miteco_dataset_type_hvd_dataset(field, schema):
    """Validator for MITECO general type HVD dataset.

    This validator checks the `miteco_dataset_type` field and sets the 
    `hvd_category` field accordingly. If `miteco_dataset_type` is 
    'http://publications.europa.eu/resource/authority/dataset-type/GEOSPATIAL', it sets `hvd_category` to `INSPIRE_HVD_CATEGORY`. 
    Otherwise, it sets `hvd_category` to `MITECO_DEFAULT_HVD_CATEGORY`. 
    Additionally, it ensures that `DCAT_AP_HVD_CATEGORY_LEGISLATION` is 
    included in the `applicable_legislation_key` list.

    Args:
        field (str): The field name being validated.
        schema (dict): The schema definition.

    Returns:
        function: The validator function.
    """
    def validator(key, data, errors, context):
        hvd_category = data.get(key)
        applicable_legislation_key = ('applicable_legislation_key', )
        miteco_dataset_type = data.get(('miteco_dataset_type', ))

        if not hvd_category or miteco_dataset_type in MITECO_DEFAULT_GENERAL_TYPE_HVDS:
            if miteco_dataset_type == MITECO_INSPIRE_GENERAL_TYPE:
                data[key] = INSPIRE_HVD_CATEGORY
            else:
                data[key] = MITECO_DEFAULT_HVD_CATEGORY

            if isinstance(data.get(applicable_legislation_key), list):
                if DCAT_AP_HVD_CATEGORY_LEGISLATION not in data[applicable_legislation_key]:
                    data[applicable_legislation_key].append(DCAT_AP_HVD_CATEGORY_LEGISLATION)
            else:
                if data.get(applicable_legislation_key) != DCAT_AP_HVD_CATEGORY_LEGISLATION:
                    data[applicable_legislation_key] = [DCAT_AP_HVD_CATEGORY_LEGISLATION]

    return validator

@scheming_validator
@validator
def miteco_miteco_contact_point(field, schema):
    pass