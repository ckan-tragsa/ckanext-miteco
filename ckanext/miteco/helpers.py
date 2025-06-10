import json
import logging
import typing
from functools import lru_cache

import ckan.lib.helpers as h
import ckan.plugins as p
import ckan.authz as authz
from ckan import model
import ckan.logic as logic
import ckanext.schemingdcat.helpers as sh
import ckanext.hierarchy.helpers as hh
from ckan.common import request

log = logging.getLogger(__name__)

all_helpers = {}
_high_value_data_statistics = {}
_hvd_mapping = {'http://data.europa.eu/bna/c_164e0bf5': {'en': 'Meteorological', 'es': 'Meteorología'}, 'http://data.europa.eu/bna/c_13e3cf16': {'en': 'NWP model data', 'es': 'Datos del modelo PMN'}, 'http://data.europa.eu/bna/c_36807466': {'en': 'Climate data: validated observations', 'es': 'Datos climáticos: observaciones validadas'}, 'http://data.europa.eu/bna/c_3af3368c': {'en': 'Observations data measured by weather stations', 'es': 'Datos de observaciones medidos por estaciones meteorológicas'}, 'http://data.europa.eu/bna/c_be47b010': {'en': 'Weather alerts', 'es': 'Avisos meteorológicos'}, 'http://data.europa.eu/bna/c_d13a4420': {'en': 'Radar data', 'es': 'Datos de radares'}, 'http://data.europa.eu/bna/c_a9135398': {'en': 'Companies and company ownership', 'es': 'Sociedades y propiedad de sociedades'}, 'http://data.europa.eu/bna/c_56a1bf47': {'en': 'Basic company information: key attributes', 'es': 'Información de contacto básica: principales atributos'}, 'http://data.europa.eu/bna/c_8f0fac04': {'en': 'Company documents and accounts', 'es': 'Documentos y cuentas de la empresa'}, 'http://data.europa.eu/bna/c_ac64a52d': {'en': 'Geospatial', 'es': 'Geoespacial'}, 'http://data.europa.eu/bna/c_60182062': {'en': 'Buildings', 'es': 'Edificios'}, 'http://data.europa.eu/bna/c_642643e6': {'en': 'Agricultural parcels', 'es': 'Parcelas agrícolas'}, 'http://data.europa.eu/bna/c_6a3f6896': {'en': 'Cadastral parcels', 'es': 'Parcelas catastrales'}, 'http://data.europa.eu/bna/c_6c2bb82d': {'en': 'Geographical names', 'es': 'Nombres geográficos'}, 'http://data.europa.eu/bna/c_9427236f': {'en': 'Administrative units', 'es': 'Unidades administrativas'}, 'http://data.europa.eu/bna/c_c3de25e4': {'en': 'Addresses', 'es': 'Direcciones'}, 'http://data.europa.eu/bna/c_fbd2fc3f': {'en': 'Reference parcels', 'es': 'Parcelas de referencia'}, 'http://data.europa.eu/bna/c_b79e35eb': {'en': 'Mobility', 'es': 'Movilidad'}, 'http://data.europa.eu/bna/c_4b74ea13': {'en': 'Transport networks', 'es': 'Redes de transporte'}, 'http://data.europa.eu/bna/c_b151a0ba': {'en': 'Inland waterways datasets', 'es': 'Conjuntos de datos sobre vías navegables interiores'}, 'http://data.europa.eu/bna/c_dd313021': {'en': 'Earth observation and environment', 'es': 'Observación de la Tierra y medio ambiente'}, 'http://data.europa.eu/bna/c_06b1eec4': {'en': 'Hydrography', 'es': 'Hidrografía'}, 'http://data.europa.eu/bna/c_315692ad': {'en': 'Elevation', 'es': 'Elevaciones'}, 'http://data.europa.eu/bna/c_38933a65': {'en': 'Waste', 'es': 'Residuos'}, 'http://data.europa.eu/bna/c_43f88346': {'en': 'Water', 'es': 'Agua'}, 'http://data.europa.eu/bna/c_4ba9548e': {'en': 'Emissions', 'es': 'Emisiones'}, 'http://data.europa.eu/bna/c_4d63300b': {'en': 'Horizontal legislation', 'es': 'Legislación horizontal'}, 'http://data.europa.eu/bna/c_4dd389c5': {'en': 'Mineral resources', 'es': 'Recursos minerales'}, 'http://data.europa.eu/bna/c_59c93ba5': {'en': 'Production and industrial facilities', 'es': 'Instalaciones de producción e industriales'}, 'http://data.europa.eu/bna/c_59e64dd4': {'en': 'Climate', 'es': 'Clima'}, 'http://data.europa.eu/bna/c_63b37dd4': {'en': 'Air', 'es': 'Aire'}, 'http://data.europa.eu/bna/c_63be22bd': {'en': 'Natural risk zones', 'es': 'Zonas de riesgos naturales'}, 'http://data.europa.eu/bna/c_793164b6': {'en': 'Species distribution', 'es': 'Distribución de las especies'}, 'http://data.europa.eu/bna/c_7b8fbb64': {'en': 'Environmental monitoring facilities', 'es': 'Instalaciones de observación del medio ambiente'}, 'http://data.europa.eu/bna/c_83aa10a6': {'en': 'Protected sites', 'es': 'Lugares protegidos'}, 'http://data.europa.eu/bna/c_87a129d9': {'en': 'Soil', 'es': 'Suelo'}, 'http://data.europa.eu/bna/c_91185a85': {'en': 'Orthoimagery', 'es': 'Ortoimágenes'}, 'http://data.europa.eu/bna/c_ad9ae929': {'en': 'Land use', 'es': 'Uso del suelo'}, 'http://data.europa.eu/bna/c_af646f5b': {'en': 'Area management / restriction / regulation zones & reporting units', 'es': 'Zonas sujetas a ordenación, a restricciones o reglamentaciones y unidades de notificación'}, 'http://data.europa.eu/bna/c_b21e1296': {'en': 'Land cover', 'es': 'Cubierta terrestre'}, 'http://data.europa.eu/bna/c_b40e6d46': {'en': 'Oceanographic geographical features', 'es': 'Rasgos geográficos oceanográficos'}, 'http://data.europa.eu/bna/c_b7de66cd': {'en': 'Energy resources', 'es': 'Recursos energéticos'}, 'http://data.europa.eu/bna/c_b7f6a4f3': {'en': 'Nature preservation and biodiversity', 'es': 'Protección de la naturaleza y biodiversidad'}, 'http://data.europa.eu/bna/c_c3919aec': {'en': 'Habitats and biotopes', 'es': 'Hábitats y biotopos'}, 'http://data.europa.eu/bna/c_c873f344': {'en': 'Bio-geographical regions', 'es': 'Regiones biogeográficas'}, 'http://data.europa.eu/bna/c_e3f55603': {'en': 'Geology', 'es': 'Geología'}, 'http://data.europa.eu/bna/c_e4358335': {'en': 'Noise', 'es': 'Ruido'}, 'http://data.europa.eu/bna/c_f399050e': {'en': 'Sea regions', 'es': 'Regiones marinas'}, 'http://data.europa.eu/bna/c_e1da4e07': {'en': 'Statistics', 'es': 'Estadística'}, 'http://data.europa.eu/bna/c_04bf94a3': {'en': 'Poverty', 'es': 'Pobreza'}, 'http://data.europa.eu/bna/c_20cd11bb': {'en': 'EU International trade in goods statistics – exports and imports breakdowns simultaneously by partner, product and flow', 'es': 'Estadísticas de la UE sobre comercio internacional de bienes: exportaciones e importaciones desgloses simultáneos por socio, producto y flujo'}, 'http://data.europa.eu/bna/c_23385471': {'en': 'Potential labour force', 'es': 'Mano de obra potencial'}, 'http://data.europa.eu/bna/c_2aed31f9': {'en': 'Industrial producer price index breakdowns by activity', 'es': 'Desgloses del índice de precios industriales por actividad'}, 'http://data.europa.eu/bna/c_317b9493': {'en': 'Population, Fertility, Mortality', 'es': 'Población, fertilidad, mortalidad'}, 'http://data.europa.eu/bna/c_34abf8c1': {'en': 'Industrial production', 'es': 'Producción industrial'}, 'http://data.europa.eu/bna/c_424bb0b4': {'en': 'Current healthcare expenditure', 'es': 'Gasto sanitario corriente'}, 'http://data.europa.eu/bna/c_4ac557e7': {'en': 'Government expenditure and revenue', 'es': 'Gastos e ingresos públicos'}, 'http://data.europa.eu/bna/c_4acb6bf3': {'en': 'Mortality', 'es': 'Mortalidad'}, 'http://data.europa.eu/bna/c_59627af3': {'en': 'National accounts – key indicators on households', 'es': 'Cuentas nacionales: principales indicadores sobre los hogares'}, 'http://data.europa.eu/bna/c_6a7250c': {'en': 'Fertility', 'es': 'Fertilidad'}, 'http://data.europa.eu/bna/c_92874eb2': {'en': 'Environmental accounts and statistics', 'es': 'Cuentas y estadísticas medioambientales'}, 'http://data.europa.eu/bna/c_95da87c7': {'en': 'National accounts – key indicators on corporations', 'es': 'Cuentas nacionales: principales indicadores sobre las empresas'}, 'http://data.europa.eu/bna/c_a2c6dcd8': {'en': 'Employment', 'es': 'Empleo'}, 'http://data.europa.eu/bna/c_a3767648': {'en': 'Tourism flows in Europe', 'es': 'Flujos turísticos en Europa'}, 'http://data.europa.eu/bna/c_a49ec591': {'en': 'Volume of sales by activity', 'es': 'Volumen de ventas por actividad'}, 'http://data.europa.eu/bna/c_a8b937c4': {'en': 'Inequality', 'es': 'Desigualdad'}, 'http://data.europa.eu/bna/c_b72b721f': {'en': 'National accounts – GDP main aggregates', 'es': 'Cuentas nacionales — principales agregados del PIB'}, 'http://data.europa.eu/bna/c_c0022235': {'en': 'Harmonised Indices of consumer prices', 'es': 'Índice de precios de consumo armonizados'}, 'http://data.europa.eu/bna/c_dd8f4797': {'en': 'Consolidated government gross debt', 'es': 'Deuda bruta consolidada de las Administraciones Públicas'}, 'http://data.europa.eu/bna/c_f2b50efd': {'en': 'Population', 'es': 'Población'}, 'http://data.europa.eu/bna/c_fd4e881c': {'en': 'Unemployment', 'es': 'Desempleo'}}


def helper(fn):
    """Collect helper functions into the ckanext.schemingdcat.all_helpers dictionary.

    Args:
        fn (function): The helper function to add to the dictionary.

    Returns:
        function: The helper function.
    """
    all_helpers[fn.__name__] = fn
    return fn

@helper
def miteco_check_miteco_identifier(miteco_identifier):
    '''
    Returns the current package count for datasets associated with the given
    source id
    '''
    fq = '+extras_miteco_identifier:"{0}"'.format(miteco_identifier)
    search_dict = {'fq': fq, 'include_private': True}
    context = {'model': model, 'session': model.Session}
    result = logic.get_action('package_search')(context, search_dict)
    return result.get('count', 0)


@helper
def miteco_get_high_value_data_statistics():
    """
    Retrieves Open Data portal statistics including counts of datasets, distributions, groups, organizations, tags, spatial datasets, and endpoints.

    Args:
        stat_type (str, optional): The type of statistics to filter by. If None, all statistics are returned.

    Returns:
        dict: A dictionary containing the counts of various site elements, with keys as the 'id' and values as dictionaries containing 'value', 'label', 'icon', 'stat_count', and 'stat_type'.
    """
    global _high_value_data_statistics

    # Retrieve the statistics list from the action
    stats_list = sh.schemingdcat_get_theme_statistics(theme_field="hvd_category",icons_dir="/images/icons/hvd_category/")
    log.debug('stats_list : %s',stats_list)
    # Convert the list of dictionaries to a summarized dictionary
    for stat in stats_list:
        stat_id = _hvd_mapping[stat['value']]['en']
        
        if stat_id in _high_value_data_statistics:
            # Update only the stat_count if the entry already exists in the cache
            _high_value_data_statistics[stat_id]['stat_count'] = stat['count']
        else:
            # Add new entry to the cache
            _high_value_data_statistics[stat_id] = {
                'value': stat['value'],
                'label': _hvd_mapping[stat['value']],
                'icon': sh.schemingdcat_get_icon(icons_dir="images/icons/hvd_category/",choice_value=stat['label']),
                'stat_count': stat['count'],
                'stat_type': 'theme'
            }

    #log.debug('high value data statistics: %s',_high_value_data_statistics)
    return _high_value_data_statistics

@helper
def get_hv_datasets(count=10, return_count=True):
    """
    This helper function retrieves a specified number of featured datasets from the CKAN instance. 
    It uses the 'package_search' action of the CKAN logic layer to perform a search with specific parameters.
    
    Parameters:
    count (int): The number of featured datasets to retrieve. Default is 10.
    return_count (bool): If True, returns the count of featured datasets. If False, returns the detailed information. Default is False.

    Returns:
    int or list: If return_count is True, returns the count of featured datasets. Otherwise, returns a list of dictionaries, each representing a featured dataset.
    """
    fq = '+hvd_category:*'
    search_dict = {
        'fq': fq, 
        'fl': 'extras_hvd_category',
        'rows': count
    }
    context = {'model': model, 'session': model.Session}
    result = logic.get_action('package_search')(context, search_dict)
    
    log.debug('result : %s',result)
    if return_count:
        return result['count']
    else:
        return result['results']



@helper
def miteco_get_tags():
    """this helper function returns all the tags in the portal

    parameters:

    returns: 
        list of tags

    """

    return logic.get_action('tag_list')()

@helper
def group_tree_miteco(organizations=[], type_='organization'):
    full_tree_list = p.toolkit.get_action('group_tree')({}, {'type': type_})

    # Añadir lógica de ordenación basada en 'title asc/desc'
    sort = request.params.get('sort', 'title asc').strip().lower()
    reverse = sort == 'title desc'
    def sort_nodes(nodes):
        sorted_nodes = sorted(
            nodes,
            key=lambda n: n.get('name', '').lower(),
            reverse=reverse
        )
        for node in sorted_nodes:
            if node.get('children'):
                node['children'] = sort_nodes(node['children'])
        return sorted_nodes

    if not organizations:
        return sort_nodes(full_tree_list)
    else:
        filtered_tree_list = group_tree_filter_miteco(organizations, full_tree_list)
        return sort_nodes(filtered_tree_list)
    
@helper   
def group_tree_highlight_miteco(organizations, group_tree_list):
    selected_names = {o.get('name', None) for o in organizations if o.get('name')}

    def traverse_and_mark(node):
        # Recorremos hijos primero (postorden)
        matched = node.get('name') in selected_names
        highlighted_child = False

        children = node.get('children', [])
        for child in children:
            if traverse_and_mark(child):
                highlighted_child = True

        # Marcar el nodo si coincide directamente o algún hijo lo hace
        node['highlighted'] = matched or highlighted_child
        return node['highlighted']

    # Aplicamos sobre el árbol completo
    for top_node in group_tree_list:
        traverse_and_mark(top_node)

    return group_tree_list

@helper
def group_tree_filter_miteco(organizations, group_tree_list, highlight=False):
    # this method leaves only the sections of the tree corresponding to the
    # list since it was developed for the users, all children organizations
    # from the organizations in the list are included
    def traverse_select_highlighted(group_tree, selection=[], highlight=False):
        # add highlighted branches to the filtered tree
        if group_tree['highlighted']:
            # add to the selection and remove highlighting if necessary
            if highlight:
                selection += [group_tree]
            else:
                selection += hh.group_tree_highlight([], [group_tree])
        else:
            # check if there is any highlighted child tree
            for child in group_tree.get('children', []):
                traverse_select_highlighted(child, selection)

    filtered_tree = []
    # first highlights all the organizations from the list in the three
    for group in hh.group_tree_highlight(organizations, group_tree_list):
        traverse_select_highlighted(group, filtered_tree, highlight)

    return filtered_tree

