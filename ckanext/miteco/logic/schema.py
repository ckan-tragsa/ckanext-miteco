import re

import ckan.plugins as p

def _modify_package_schema(self, schema):
    schema.update(
        {
            "tags": [
                p.toolkit.get_validator("ignore_missing"),
                normalize_tags,
            ]
        }
    )
    return schema

def create_package_schema(self):
    schema = super(OgdchShowcasePlugin, self).create_package_schema()
    schema = self._modify_package_schema(schema)
    return schema

def update_package_schema(self):
    schema = super(OgdchShowcasePlugin, self).update_package_schema()
    schema = self._modify_package_schema(schema)
    return schema

def normalize_tags(self, tags):
    def normalize_string(s):
        # Convertir a minúsculas
        s = s.lower()
        # Eliminar caracteres no permitidos (letras españolas, números, guiones, guiones bajos y puntos)
        s = re.sub(r'[^a-záéíóúüñ0-9\-_\.]', '', s)
        # Reemplazar espacios por guiones
        s = s.replace(' ', '-')
        # Eliminar espacios al inicio y al final
        s = s.strip()
        # Limitar a 30 caracteres
        s = s[:30]
        return s
    
    if tags:
        normalized_tags = []
        if isinstance(tags, list):
            for item in tags:
                normalized_item = normalize_string(item)
                normalized_tags.append(normalized_item)
        elif isinstance(tags, str):
            items = tags.split(',')
            for item in items:
                normalized_item = normalize_string(item)
                normalized_tags.append(normalized_item)
    
    return normalized_tags