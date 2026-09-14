import os
from importlib.resources import files
from ckanext.spatial.harvested_metadata import ISODocument
from ckanext.spatial.validation.validation import XsdValidator

from lxml import etree

log = __import__("logging").getLogger(__name__)


class ISO19139InspireSchema(XsdValidator):
    name = 'inspire'
    title = 'INSPIRE XSD Schema'

    @classmethod
    def is_valid(cls, xml):
        xsd_path = 'xml/iso19139inspire'
        gmx_xsd_filepath = os.path.join(os.path.dirname(__file__),
                                        xsd_path, 'gmd-csw.xsd')
        xsd_name = 'Dataset schema (gmd.xsd)'
        is_valid, errors = cls._is_valid(xml, gmx_xsd_filepath, xsd_name)
        if not is_valid:
            # TODO: not sure if we need this one,
            # keeping for backwards compatibility
            errors.insert(0, ('{0} Validation Error'.format(xsd_name), None))
        return is_valid, errors