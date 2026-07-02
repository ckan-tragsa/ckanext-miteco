import uuid
import json
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging
from hashlib import md5
from time import asctime, localtime

from six import text_type
import sqlalchemy as sa
from sqlalchemy.orm import class_mapper
try:
    from sqlalchemy.engine import Row
except ImportError:
    try:
        from sqlalchemy.engine.result import RowProxy as Row
    except ImportError:
        from sqlalchemy.engine.base import RowProxy as Row


from ckan import model
import ckan.logic as logic
from ckan.model.domain_object import DomainObject


log = logging.getLogger(__name__)

inspire_xml_table = None

def make_uuid():
    return text_type(uuid.uuid4())

def setup():
    """
    Sets up the Inspire xml table if it does not already exist.

    This function checks if the `inspire_xml_table` is defined and creates it if it does not exist.
    It ensures that the table is defined in the database and logs the action.

    Returns:
        None
    """
    if inspire_xml_table is None:
        define_tables()

    if not inspire_xml_table.exists():
        inspire_xml_table.create(checkfirst=True)
        log.debug('Inspire xml table defined in DB')

def clean():
    """
    Cleans the Inspire xml table by dropping it if it exists and recreating it from scratch.

    This function ensures that the `schemingdcat_Inspire xml` table is reset to an empty state.
    It drops the existing table and then calls `setup()` to recreate it.

    Returns:
        None    

    """
    global inspire_xml_table

    try:
        if inspire_xml_table is not None and inspire_xml_table.exists():
            inspire_xml_table.drop(checkfirst=True)
            log.debug('Inspire xml table dropped from DB')
    except Exception as e:
        log.error('Error dropping Inspire xml table: %s', e)
    
    setup()
    

def define_tables():
    """
    Defines the statistics table in the database and maps it to the `InspireHandler` class.

    This function creates a global `inspire_xml_table` with the necessary columns if it does not already exist.
    It then maps the `InspireHandler` class to this table using SQLAlchemy's mapper.
    """
    global inspire_xml_table

    inspire_xml_table = sa.Table(
        'inspire_xml',
        model.meta.metadata,
        sa.Column('md5', sa.types.UnicodeText, primary_key=True, nullable=False),
        sa.Column('uuid', sa.types.UnicodeText, primary_key=False),
        sa.Column('time', sa.types.Time, nullable=False),
        sa.Column('xml', sa.types.UnicodeText, nullable=False)
    )

    model.meta.mapper(
        InspireHandler,
        inspire_xml_table,
    )

class InspireHandler(DomainObject):
    """
    class to handle whole iso19115 documents inside the portal database
    """

    @classmethod
    def get(cls, uuid=None, md5=None) -> any:
        """obtains a single spatial document from the database"""
        query = model.Session(cls).autoflush(false)
        if md5:
            return query.filter_by(f"md5={md5}").first()
        elif uuid:
            return query.filter_by(f"uuid='{uuid}'").order_by('inspire_xml.time').first()
        else:
            raise ValueError

def setDocument(uuid, xml):
    """
    loads a single spatial document into the database
    the primary key is set to the md5 generated from a string created by appending the local time to the UUID
    This is meant to keep copies of old versions of the spatial document in the database
    """
    timestamp = localtime()
    hashstring = uuid + asctime(timestamp)
    pk = md5(hashstring.decode(),usedforsecurity=False).hexdigest().encode("utf8")
    row = {
        "md5":pk,
        "uuid":uuid,
        "time": timestamp,
        "xml":xml
        }
    model.Session.add(row)
    try:
        model.Session.commit()
        log.debug("spatial xml loaded")
    except Exception as e:
        log.error("Error loading spatial xml: %s", e)
        model.Session.rollback()