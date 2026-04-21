import ckan.plugins.toolkit as toolkit
import ckan.model as model
from ckan.common import config

from ckanext.miteco.processor import AtomSerializer


def dataset_atom_page(_id):
    context = {
    'model': model,
    'session': model.Session,
    'user': toolkit.c.user,
    'for_view': True
    }
    data_dict = {'id': _id}
    dataset = toolkit.get_action('package_show')(context, data_dict)

    serializer = AtomSerializer()
    atom = serializer.serialize_dataset(
        dataset_dict=dataset,
        site_url=config.get("ckan.site_url")
    )

    return atom

def catalog_atom_page():
    context = {
    'model': model,
    'session': model.Session,
    'user': toolkit.c.user,
    'for_view': True
    }
    data_dict = {
    "rows": 1000
    }
    datasets = toolkit.get_action('package_search')(context, data_dict)['results']

    serializer = AtomSerializer()

    catalog_dict = {
        "title": config.get("ckan.site_title"),
        "url": config.get("ckan.site_url"),
    }

    atom = serializer.serialize_catalog(
        catalog_dict=catalog_dict,
        dataset_dicts=datasets,
        site_url=config.get("ckan.site_url")
    )
    return atom
