"""Use SchemingDCAT's stylesheet with local INSPIRE import overrides."""
from pathlib import Path

from lxml import etree
from saxonche import PySaxonProcessor
from ckanext.schemingdcat.config import XLST_MAPPINGS_DIR


def transform(xml):
    stylesheet = Path(__file__).parent / 'xslt' / 'mapa-import.xsl'
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    tree = etree.parse(str(stylesheet), parser)
    imported = tree.getroot().find('{http://www.w3.org/1999/XSL/Transform}import')
    imported.set('href', (Path(XLST_MAPPINGS_DIR) / 'custom-transform.xsl').resolve().as_uri())
    with PySaxonProcessor(license=False) as processor:
        executable = processor.new_xslt30_processor().compile_stylesheet(
            stylesheet_text=etree.tostring(tree, encoding='unicode'))
        source = processor.parse_xml(xml_text=xml)
        return executable.transform_to_string(xdm_node=source)
