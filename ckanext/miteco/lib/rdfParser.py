import logging
import rdflib
import rdflib.parser
from ckan.plugins.toolkit import get_action

log = logging.getLogger(__name__)

class mitecoRDFParser:
    def rdf_to_dataset(self):
        mapping = self._generate_mapping()
        datasets = self._extract_datasets(mapping)
        
        pass

    def _generate_mapping(self):
        schema = get_action(scheming_dataset_schema_show)(None, {"type":"dataset"})
        log.debug(schema)
        pass

    def _extract_datasets(self):
        pass

    def _extract_resources(self):
        pass
