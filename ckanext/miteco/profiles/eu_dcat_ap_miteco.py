import json
import logging
from ckanext.miteco.inspire.fields import read_fields, write_fields

from rdflib import URIRef, BNode, Literal
from ckanext.dcat.profiles.base import URIRefOrLiteral, CleanedURIRef, Namespace

from ckanext.schemingdcat.profiles.dcat_ap.eu_dcat_ap_3 import EuDCATAP3Profile
from ckanext.schemingdcat.profiles.geodcat_ap.eu_geodcat_ap_2 import EuGeoDCATAP2Profile
from ckanext.schemingdcat.profiles.eu_dcat_ap_scheming import EuDCATAPSchemingDCATProfile
from ckanext.schemingdcat.profiles.dcat_config import (
    # Vocabs
    RDF,
    XSD,
    SKOS,
    SCHEMA,
    RDFS,
    DCAT,
    DCATAP,
    DCT,
    ADMS,
    VCARD,
    FOAF,
    LOCN,
    GEODCATAP,
    )
DCTERMS = Namespace("http://purl.org/dc/terms/")

from ckanext.miteco.config import RDF_DATASET_TEMPLATE, RDF_PREFIX

log = logging.getLogger(__name__)

class MitecoDCATAPProfile(EuGeoDCATAP2Profile, EuDCATAP3Profile, EuDCATAPSchemingDCATProfile):
    """
    Custom ckanext-dcat euro_dcat_ap_scheming profile. https://github.com/ckan/ckanext-dcat/blob/master/ckanext/dcat/profiles/euro_dcat_ap_scheming.py
    
    Notes: 
        **EuropeanDCATAPSchemingProfile**: This is a compatibilty profile meant to add support for ckanext-scheming to the
        existing `euro_dcat_ap` and `euro_dcat_ap_2` profiles.
        It does not add or remove any properties from these profiles, it just transforms the
        resulting dataset_dict so it is compatible with a ckanext-scheming schema
    """
    def parse_dataset(self, dataset_dict, dataset_ref):
        
        dataset_dict = self._miteco_dataset_set_defaults(dataset_dict, dataset_ref)

        # Call base method for common properties
        dataset_dict = self._parse_dataset_base(dataset_dict, dataset_ref)

        # DCAT AP v2 properties also applied to higher versions
        dataset_dict = self._parse_dataset_v2(dataset_dict, dataset_ref)

        # DCAT AP v2 scheming fields
        dataset_dict = self._parse_dataset_v2_scheming(dataset_dict, dataset_ref)

        # GeoDCAT-AP 2 properties
        dataset_dict = self._parse_dataset_geodcat_ap_v2(dataset_dict, dataset_ref)

        dataset_dict = self._parse_dataset_miteco(dataset_dict, dataset_ref)

        self._miteco_map_values(dataset_dict, dataset_ref)

        return read_fields(self, dataset_dict, dataset_ref)

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        EuGeoDCATAP2Profile.graph_from_dataset(self, dataset_dict, dataset_ref)
        self._graph_from_dataset_v2_scheming(dataset_dict, dataset_ref)
        write_fields(self, dataset_dict, dataset_ref)

    def _miteco_dataset_set_defaults(self, dataset_dict, dataset_ref):
        dataset_dict.update(RDF_DATASET_TEMPLATE)
        return dataset_dict
    
    def _parse_dataset_miteco(self, dataset_dict, dataset_ref):
        #log.debug(dataset_dict)
        value = self.g.query("".join([RDF_PREFIX,
                             f"""
                                SELECT ?id
                                WHERE{{
                                    <{dataset_ref}> foaf:isPrimaryTopicOf ?node .
                                    ?node dct:identifier ?id
                                }}
                                """]))
        if value:
            for row in value:
                dataset_dict['id'] = str(row['id'])

        for key, predicate in (
            ("topic", GEODCATAP.topicCategory),
        ):
            value = self._object_value(dataset_ref, predicate)
            if value:
                dataset_dict[key] = value

        return dataset_dict
    
    def _miteco_map_values(self, dataset_dict, dataset_ref):
        rules = {
            "inspire_id": "identifier"
        }
        for rule in rules.keys():
            dataset_dict[rule] = dataset_dict.pop(rules[rule], None)
            

    @staticmethod
    def _not_empty_dict(data_dict):
        return any(data_dict.values())
