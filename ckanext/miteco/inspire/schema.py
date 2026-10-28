"""Validation adaptations confined to package writes by the INSPIRE action.

The MITECO schema uses named factories that delegate unchanged outside the
INSPIRE import context. Validation, conversion, authorization and plugin hooks
remain in the normal CKAN action pipeline.
"""
from functools import wraps

from ckan.plugins import toolkit


_ALWAYS_PRESERVE = {
    'schemingdcat_contact_as_default_publisher',
    'schemingdcat_access_url_if_empty_same_as_url',
    'schemingdcat_download_url_if_empty_same_as_url',
}
_DATE_DEFAULTS = {'schemingdcat_if_empty_datenow'}
_DEPENDENT_DEFAULTS = {
    'schemingdcat_fill_dependent_fields',
    'schemingdcat_fill_spatial_dependent_fields',
}


def _adapt_validator(original, field, factory):
    """Wrap a known factory using its explicit field definition."""
    @wraps(original)
    def imported_value(key, data, errors, context):
        if not context.get('preserve_mapped_fields'):
            return original(key, data, errors, context)
        value = data.get(key, toolkit.missing)
        if factory in _ALWAYS_PRESERVE:
            if factory == 'schemingdcat_contact_as_default_publisher' and value is toolkit.missing:
                data[key] = None
            return
        if factory in _DATE_DEFAULTS and value is not toolkit.missing:
            return
        if factory == 'schemingdcat_dataset_url' and value is not toolkit.missing and value:
            return
        if factory in _DEPENDENT_DEFAULTS:
            dependent = field.get('dependent_fields')
            if dependent:
                if value is toolkit.missing or value is None or value == '':
                    data[key] = None
                    return
                supplied = any(k[0] == dependent['field_name'] for k in data)
                spatial = data.get(('spatial',), toolkit.missing)
                if factory == 'schemingdcat_fill_spatial_dependent_fields':
                    supplied = supplied or (spatial is not toolkit.missing and bool(spatial))
                if supplied:
                    return
        return original(key, data, errors, context)

    return imported_value


def get_import_validators():
    """Named Scheming factories used only by the MITECO schema.

    Scheming expands its own validators during plugin validation, so adapting
    the earlier core NAVL schema is insufficient. Register explicit factories
    through IValidators instead, without replacing shared validator names.
    """
    from ckanext.schemingdcat import validators
    result = {}
    names = _ALWAYS_PRESERVE | _DATE_DEFAULTS | _DEPENDENT_DEFAULTS | {'schemingdcat_dataset_url'}
    for name in names:
        factory = getattr(validators, name)

        def make_factory(factory):
            @wraps(factory)
            def local_factory(field, schema):
                return _adapt_validator(factory(field, schema), field, factory.__name__)
            return local_factory

        result[name.replace('schemingdcat_', 'miteco_inspire_', 1)] = make_factory(factory)
    result['miteco_inspire_omit_invalid'] = omit_invalid_import_value
    return result


def omit_invalid_import_value(key, data, errors, context):
    """Handle a rejected imported field at the end of its normal NAVL chain.

    Other fields and ordinary CKAN edits keep their original validation errors.
    The caller supplies the authorized existing package before merging XML data.
    """
    if not (context.get('preserve_mapped_fields') and context.get('_inspire_pushing')):
        return
    if not errors.get(key):
        return
    value = data.get(key)
    existing = context.get('_inspire_existing_pkg') or {}
    if len(key) == 3 and key[0] == 'resources':
        resource_id = data.get(key[:2] + ('id',))
        existing = next((resource for resource in existing.get('resources', [])
                         if resource_id and resource.get('id') == resource_id), {})
    elif len(key) != 1:
        return
    field = '.'.join(str(part) for part in key)
    warnings = context.get('_inspire_warnings')
    # Never suppress an error if the importing action cannot return its warning.
    if warnings is None:
        return
    warning = {'field': field, 'value': value,
               'message': toolkit._('El valor del XML no es representable en este campo de CKAN y se ha omitido. Se conserva el valor CKAN existente, si lo hay, y el dato original permanece en el XML descargable.')}
    if warning not in warnings:
        warnings.append(warning)
    errors[key][:] = []
    data[key] = existing.get(key[-1])


def package_action(name, context, data):
    """Keep normal plugin validation; the MITECO schema selects local factories."""
    if name not in ('package_create', 'package_update', 'package_patch'):
        raise ValueError('Unsupported INSPIRE package action')
    return toolkit.get_action(name)(context, data)


def filter_import_frequency(context, data):
    """Omit unrepresentable frequencies only from the INSPIRE import payload."""
    value = data.get('frequency')
    if not value:
        return []
    schema = toolkit.get_action('scheming_dataset_schema_show')(
        context, {'type': data.get('type') or 'dataset'})
    field = next((field for field in schema['dataset_fields']
                  if field['field_name'] == 'frequency'), None)
    if field is not None and ('choices' not in field or
                             value in {choice['value'] for choice in field['choices']}):
        return []
    data.pop('frequency', None)
    # An extra with the same name must not reintroduce the rejected value.
    data['extras'] = [extra for extra in data.get('extras', [])
                      if extra.get('key') != 'frequency']
    return [{'field': 'frequency', 'value': value,
             'message': toolkit._('The XML update frequency cannot be represented in the CKAN schema. It has been omitted from the imported fields and remains unchanged in the original XML. Any existing CKAN frequency is preserved.')}]
