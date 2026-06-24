
import dateutil.parser
from dateutil.tz import tzutc
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

INVALID_XML_RE = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F]"
)

def clean_xml_text(text):
    if not text:
        return text
    return INVALID_XML_RE.sub("", text)


def parse_date(date_str: str):
    """Parsea una cadena de fecha y asegura que tenga timezone (requerido por feedgen)."""
    if not date_str:
        return None
    dt = dateutil.parser.parse(date_str)
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=tzutc())
    return dt


def build_entry_id(pkg: dict, site_url: str) -> str:
    """Construye el ID único de la entrada ATOM."""
    return pkg.get("url") if pkg.get("url") else f"{site_url}/dataset/{pkg['name']}"



class AtomSerializer:
    def __init__(self):
        pass

    def _add_resource_entries(self, fg, dataset_dict, site_url):

        for r in dataset_dict.get("resources", []):
            if not r.get("url"):
                continue

            fe = fg.add_entry()

            resource_url = r["url"]

            # ID = link de descarga
            fe.id(resource_url)

            # Link alternate = descarga
            fe.link(
                href=resource_url,
                rel="alternate",
                type=r.get("mimetype") or "application/octet-stream",
                title=r.get("name")
            )

            # Title del recurso (o dataset si no hay)
            fe.title(clean_xml_text(r.get("name") or dataset_dict.get("title")))

            # Updated
            updated = (
                r.get("last_modified")
                or dataset_dict.get("metadata_modified")
                or dataset_dict.get("metadata_created")
            )

            dt = parse_date(updated) or datetime.now(tzutc())
            fe.updated(dt)

            # Summary opcional
            if r.get("description"):
                fe.summary(clean_xml_text(r["description"]))


    def _add_dataset_entry(self, fg, dataset_dict, site_url):

        fe = fg.add_entry()
        dataset_feed_url = f"{site_url}/catalogo/miteco/dataset/{dataset_dict['name']}.atom"
    

        # ID
        fe.id(dataset_feed_url)


        # Link al atom del dataset
        fe.link(
            href=dataset_feed_url,
            rel="alternate",
            type="application/atom+xml"
        )

        dataset_url = f"{site_url}/catalogo/dataset/{dataset_dict['name']}"
        fe.link(
            href=dataset_url,
            rel="related",
            type="text/html"
        )

        # Title
        fe.title(clean_xml_text(dataset_dict.get("title") or dataset_dict["name"]))

        # Updated
        updated = (
            dataset_dict.get("metadata_modified")
            or dataset_dict.get("metadata_created")
        )

        dt = parse_date(updated) or datetime.now(tzutc())
        fe.updated(dt)

        # Summary
        if dataset_dict.get("notes"):
            fe.summary(clean_xml_text(dataset_dict["notes"]))

    
                



    def serialize_dataset(self, dataset_dict, site_url):
        fg = FeedGenerator()

        dataset_feed_url = f"{site_url}/catalogo/miteco/dataset/{dataset_dict['name']}.atom"

        dataset_url = f"{site_url}/catalogo/dataset/{dataset_dict['name']}"
    
        catalog_url = f"{site_url}/catalogo/miteco/catalog.atom"

        # ID → atom del dataset
        fg.id(dataset_feed_url)

        # Title
        fg.title(dataset_dict.get("title", "Dataset"))

        # Link self (atom)
        fg.link(href=dataset_feed_url, rel="self")

        # Link al dataset HTML
        fg.link(
            href=dataset_url,
            rel="related",
            type="text/html"
        )

        # Link al catálogo
        fg.link(href=catalog_url, rel="related", type="text/html")

        fg.updated(datetime.now(tzutc()))
        fg.language("es")

        # Author
        contacts = dataset_dict.get("contact", [])
        if contacts:
            c = contacts[0]
            fg.author({"name": c.get("name", ""), "email": c.get("email", "")})
        elif dataset_dict.get("publisher_name"):
            fg.author({
                "name": dataset_dict["publisher_name"],
                "email": dataset_dict.get("publisher_email", "")
            })

        self._add_resource_entries(fg, dataset_dict, site_url)

        return fg.atom_str(pretty=True)


    # CATALOG
    def serialize_catalog(self, catalog_dict,
                          dataset_dicts=None,
                          site_url=None):

        fg = FeedGenerator()

        catalog_url = catalog_dict.get("url") or site_url
    
        fg.id(catalog_url)
        fg.title(catalog_dict.get("title", "Catalog ATOM"))
        fg.link(href=f"{catalog_url}/catalogo/miteco/catalog.atom", rel="self")
        fg.language("es")
        fg.updated(datetime.now(tzutc()))

        if dataset_dicts:
            for dataset_dict in dataset_dicts:
                self._add_dataset_entry(fg, dataset_dict, site_url)

        return fg.atom_str(pretty=True)
 