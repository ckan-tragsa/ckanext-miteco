from ckanext.miteco.inspire import model as insp_model
from ckan.lib.navl.dictization_functions import flatten_dict, unflatten
from ckanext.schemingdcat.lib.csw_mapper.xslt_transformer import XSLTTransformer
from ckanext.dcat.processors import RDFParserException, RDFParser
from ckanext.miteco.lib.rdfParser import mitecoRDFParser
import logging, traceback
import ckan.plugins as p
import ckan.lib.helpers as h
from ckan import model
from ckanext.miteco.config import RDF_DATASET_TEMPLATE
from copy import deepcopy

log = logging.getLogger(__name__)



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
        raise p.toolkit.NotAuthorized('User must be logged in to add documents')
    

    uuid = data_dict.get('id')
    xml = data_dict.get('xml')
    org = data_dict.get('org')
    pk = insp_model.setDocument(uuid,xml)
    data, errors = xsl_fill(xml)

    user_obj = model.User.get(user)

    #hereda los permisos de package_create
    if not user_obj or not p.toolkit.check_access('package_create', context, data):
        raise p.toolkit.NotAuthorized('User %s not authorized', user)

    pk = insp_model.setDocument(uuid,xml)
    data['spatial_advanced_xml'] = pk
    data['owner_org'] =  org
    d, id_err = p.toolkit.navl_validate({"id":data['id']}, {"id":[p.toolkit.get_validator("package_id_exists")]}, context)

    
    #Desactivamos esta funcionalidad hasta el sprint 2
    '''
    if id_err:
        p.toolkit.get_action('package_create')(context, data)
    else: 
        p.toolkit.get_action('package_update')(context, data)
    '''
    
    if errors:
        return {'success':False, 'msg': f'{errors}'}
    else:
        return {'success': True, 'msg': f'{data}'}


"""
Fills the rest of fields of the schema based on the provided xml document
"""
def xsl_fill(xml):
    errors = []
    parser = RDFParser()
    profiles = ['miteco_dcat_ap']
    #log.debug('Load profiles TO RDFParser: %s', profiles)
    parser._profiles = parser._load_profiles(profiles)
    try:
        #hacemos la transformación
        transformer = XSLTTransformer("custom-transform.xsl", None)
        transformed_xml = transformer.transform(xml)
        #log.debug(transformed_xml)

        parser.parse(transformed_xml, _format='xml')         
        parsed_dataset = list(parser.datasets())[0]

        #escribimos el MD5 en el campo que corresponde
        parsed_dataset['is_spatial_advanced'] = True
        return (parsed_dataset, errors)
    
    except Exception as e:
        errors.append(f'Error parsing the XML file in upload: {e}')
        log.debug(traceback.format_exc())
        parsed_dataset = {}
        return (parsed_dataset, errors)

