import logging
from urllib.parse import urlparse

from ckan.plugins.core import SingletonPlugin, implements

from ckanext.schemingdcat.interfaces import ISchemingDCATHarvester
from ckanext.schemingdcat.helpers import schemingdcat_get_dataset_schema_required_field_names, schemingdcat_get_ckan_site_url

from ckanext.miteco.config import (
    OGC2CKAN_HARVESTER_MD_CONFIG
)

log = logging.getLogger(__name__)

class MITECOCSWHarvester(SingletonPlugin):
    '''
    A SchemingDCATCSWHarvester extended for the MTIECO deployments.
    '''

    _schema_required_fields = []

    implements(ISchemingDCATHarvester)

    def before_modify_package_dict(self, package_dict):
        log.debug('In MITECOCSWHarvester before_modify_package_dict')

        self._schema_required_fields = schemingdcat_get_dataset_schema_required_field_names()

        # Update URLs
        self._update_urls(package_dict)

        # Apply MITECO defaultlt values if required fields are empty
        self._remove_miteco_fields('miteco_identifier')
        self._apply_default_values(package_dict)

        return package_dict, []
    
    def _remove_miteco_fields(self, prefix='miteco_'):
        """
        Remove field names starting with prefix from self._schema_required_fields.
        """
        for field_group in self._schema_required_fields:
            for group_name, fields in field_group.items():
                field_group[group_name] = [field for field in fields if not field.startswith(prefix)]

    @staticmethod
    def _update_urls(package_dict, url_fields=None):
        """
        Update URL fields in the package dictionary to ensure they start with 'http://' or 'https://'.

        If a URL field does not start with 'http://' or 'https://', 'https://' is prepended to it.

        Args:
            package_dict (dict): The package dictionary where URL fields are to be updated.
            url_fields (list, optional): A list of URL fields to be updated. Defaults to ['author_url', 'contact_url', 'publisher_url', 'maintainer_url'].

        Returns:
            dict: The updated package dictionary.
        """
        if url_fields is None:
            url_fields = ['author_url', 'contact_url', 'publisher_url', 'maintainer_url']

        for field in url_fields:
            url = package_dict.get(field)
            if url:
                parsed_url = urlparse(url)
                package_dict[field] = url if parsed_url.scheme else 'https://' + url

        return package_dict
    
    def _apply_default_values(self, package_dict):
        """
        Apply default values from OGC2CKAN_HARVESTER_MD_CONFIG to package_dict
        for required fields that are missing or None.
        """
        ckan_site_url = schemingdcat_get_ckan_site_url()
    
        def substitute_ckan_site_url(value):
            if isinstance(value, str) and '{ckan_site_url}' in value:
                return value.format(ckan_site_url=ckan_site_url)
            return value
    
        for field_group in self._schema_required_fields:
            for group_name, fields in field_group.items():
                if group_name == 'dataset_fields':
                    for field in fields:
                        if field not in package_dict or package_dict[field] is None:
                            default_value = OGC2CKAN_HARVESTER_MD_CONFIG.get(field)
                            package_dict[field] = substitute_ckan_site_url(default_value)
                elif group_name == 'resource_fields':
                    for resource in package_dict.get('resources', []):
                        for field in fields:
                            if field not in resource or resource[field] is None:
                                default_value = OGC2CKAN_HARVESTER_MD_CONFIG['resources'].get(field)
                                resource[field] = substitute_ckan_site_url(default_value)