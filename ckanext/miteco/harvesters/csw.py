import json
import logging
from urllib.parse import urlparse

from ckan.plugins.core import SingletonPlugin, implements

from ckanext.schemingdcat.interfaces import ISchemingDCATHarvester
from ckanext.schemingdcat.helpers import schemingdcat_get_dataset_schema_required_field_names, schemingdcat_get_ckan_site_url

from ckanext.miteco.config import (
    OGC2CKAN_HARVESTER_MD_CONFIG
)

log = logging.getLogger(__name__)

# Date fields to preserve from the original harvest content
HARVEST_DATE_FIELDS = ['modified', 'created', 'issued']

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

        # Apply MITECO default values if required fields are empty
        self._remove_miteco_fields('miteco_identifier')
        self._apply_default_values(package_dict)

        return package_dict, []

    def before_create(self, harvest_object, package_dict, schema, harvester_tmp_dict):
        """
        Preserve original harvest dates before creating the package.
        Re-injects dates from harvest_object.content into package_dict
        to prevent them from being lost during the pipeline.
        """
        self._preserve_harvest_dates(harvest_object, package_dict)
        return None

    def before_update(self, harvest_object, package_dict, harvester_tmp_dict):
        """
        Preserve original harvest dates before updating the package.
        Re-injects dates from harvest_object.content into package_dict
        to prevent them from being lost during the pipeline.
        """
        self._preserve_harvest_dates(harvest_object, package_dict)
        return None

    @staticmethod
    def _preserve_harvest_dates(harvest_object, package_dict):
        """
        Reads the original dates from the harvest object content (JSON)
        and ensures they are present in the package_dict before saving.
        
        This avoids modifying ckanext-schemingdcat's CSWMetadataExtractor
        while still preserving the original source dates (modified, created, issued).

        Args:
            harvest_object: The HarvestObject with the original content JSON.
            package_dict (dict): The package dictionary about to be saved.
        """
        try:
            if not harvest_object or not harvest_object.content:
                return

            original_content = json.loads(harvest_object.content)

            for date_field in HARVEST_DATE_FIELDS:
                original_value = original_content.get(date_field)
                current_value = package_dict.get(date_field)

                if original_value and (not current_value or current_value != original_value):
                    log.debug(
                        'MITECO: Preserving harvest date %s: %s (was: %s)',
                        date_field, original_value, current_value
                    )
                    package_dict[date_field] = original_value

        except (ValueError, TypeError) as e:
            log.warning('MITECO: Error preserving harvest dates: %s', str(e))

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