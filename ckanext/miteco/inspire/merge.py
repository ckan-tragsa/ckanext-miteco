"""Reconcile existing CKAN values during an INSPIRE import, before saving."""
from copy import deepcopy

MULTILINGUAL_FIELDS = {'version_notes', 'title_translated', 'notes_translated', 'provenance'}


def has_text(value):
    if isinstance(value, dict):
        return any(has_text(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_text(v) for v in value)
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _key(resource):
    # Queries are part of endpoint identity. Never normalize them away.
    return resource.get('url') or resource.get('access_url') or resource.get('download_url') or ''


def merge_resources(existing, incoming, overwrite):
    """Reuse IDs only for unambiguous matches; keep complement mode additive."""
    used = set()
    result = [] if overwrite else deepcopy(existing)
    for resource in incoming:
        candidates = [i for i, old in enumerate(existing) if _key(old) == _key(resource)]
        for role in ('access_url', 'download_url', 'format'):
            if len(candidates) > 1 and resource.get(role):
                exact = [i for i in candidates if existing[i].get(role) == resource[role]]
                if exact:
                    candidates = exact
        if len(candidates) > 1:
            candidates = [i for i in candidates if existing[i].get('name') == resource.get('name')]
        if len(candidates) == 1:
            old = existing[candidates[0]]
            if old.get('name') and resource.get('name') and old['name'] != resource['name']:
                candidates = []
        if len(candidates) > 1 or any(i in used for i in candidates):
            raise ValueError('Ambiguous resource identity in INSPIRE import')
        if candidates:
            i = candidates[0]
            used.add(i)
            if overwrite:
                updated = deepcopy(existing[i])
                updated.update({k: deepcopy(v) for k, v in resource.items() if k != 'id' and v not in (None, '', [], {})})
                updated['id'] = existing[i]['id']
                result.append(updated)
        else:
            new = deepcopy(resource)
            new.pop('id', None)
            result.append(new)
    return result
