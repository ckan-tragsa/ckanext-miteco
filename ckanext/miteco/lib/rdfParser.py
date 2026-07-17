import logging, copy
from rdflib import Graph, Dataset
import ckan.plugins.toolkit as tk
from ckanext.miteco.config import RDF_DEFAULT_MAPPING, RDF_PREFIX, RDF_DATASET_TEMPLATE, RDF_RESOURCE_TEMPLATE

log = logging.getLogger(__name__)

class mitecoRDFParser:
    mapping = None
    def __init__(self):
        self._get_mapping()

    def rdf_to_dataset(self, rdf):
        if not rdf:
            raise ValueError
        g = Dataset()
        try:
            g.parse(data=rdf, format="xml" )
        except:
            raise ValueError("invalid rdf")
        dataset = self._extract_datasets(g)
        dataset['resources'] = self._extract_resources(g)
        return dataset

    def _get_mapping(self):
        schema = tk.config.get('ckanext.miteco.rdf_mapping', None)
        if not schema:
            schema = RDF_DEFAULT_MAPPING
        self.mapping = schema

    def _extract_datasets(self, rdf:Graph):
        """
        extracts all the datasets from the rdf
        """
        out = copy.deepcopy(RDF_DATASET_TEMPLATE)
        for key in self.mapping['dataset'].keys():
                if key in ["temporal_end", "temporal_start"]:
                    for row in rdf.query("".join([RDF_PREFIX,
                                        f"""
                                        select ?time
                                        where{{
                                            ?field dcat:{ {"temporal_end":"endDate","temporal_start":"startDate"}[key] } ?time .
                                        }}
                                        """])):
                        log.debug(row["time"])
                        out[key] = row["time"].split("+")[0]
                elif key == "title_translated":
                    for i in ["en","es"]:
                        for row in rdf.query("".join([RDF_PREFIX,
                                            f"""
                                            select ?title
                                            where{{
                                                ?field dct:title ?title .
                                                FILTER(lang(?title) = "{i}") .
                                                ?field a dcat:Dataset
                                            }}
                                            """])):
                            out[key][i] = row["title"]
                else:
                    for row in rdf.query("".join([RDF_PREFIX,
                                                f"""
                                                SELECT ?attrib
                                                WHERE {{
                                                    ?dataset {self.mapping['dataset'][key]} ?attrib .
                                                    ?dataset a dcat:Dataset
                                                }}
                                                """])):
                        if key in out and out[key] is list:
                            out[key].append(row["attrib"])
                        elif key == "theme":
                            out["theme_es"] = (row["attrib"])
                        elif key == "valid":
                            out[key] = row["attrib"].split("+")[0]
                        else:
                            out[key] = row["attrib"]
        return out

    def _extract_resources(self, rdf:Graph):
        out = []
        for row in rdf.query("".join([RDF_PREFIX,f"""
                            SELECT ?distribution
                            WHERE {{
                                ?dataset dcat:distribution ?distribution .
                                ?dataset a dcat:Dataset
                     }}
                            """])):
            resource = copy.deepcopy(RDF_RESOURCE_TEMPLATE)
            for key in self.mapping['resource'].keys():
                if key == "format":
                    query = "".join([RDF_PREFIX,f"""
                                        SELECT ?attrib
                                        WHERE {{
                                            ?format rdf:value ?attrib .
                                            ?Distribution dct:format ?format .
                                            ?Distribution a dcat:Distribution .
                                            FILTER ( ?Distribution = <{row["distribution"]}> )
                                        }}
                                    """])
                else:
                    query = "".join([RDF_PREFIX,f"""
                                        SELECT ?attrib
                                        WHERE {{
                                            ?Distribution {self.mapping['resource'][key]} ?attrib .
                                            ?Distribution a dcat:Distribution .
                                            FILTER ( ?Distribution = <{row["distribution"]}> )
                                            }}
                                    """])
                for drow in rdf.query(query):
                    if key == "access_url":
                        out_resource["url"] = drow["attrib"]
                    elif key == "size":
                        pass
                    else:
                        out_resource[key] = drow["attrib"]
            out.append(resource)
        return out 
