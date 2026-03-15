from copy import deepcopy


def metric(label, value, secondary=None):
    row = {
        'label': str(label),
        'value': str(value),
    }
    if secondary:
        row['secondary'] = str(secondary)
    return row


def alert(title, level='Low', secondary=''):
    normalized = str(level).strip().lower()
    if normalized not in {'high', 'medium', 'low'}:
        normalized = 'low'

    return {
        'title': str(title),
        'level': normalized.title(),
        'secondary': str(secondary or ''),
    }


def queue_item(value):
    return str(value)


def build_dashboard_payload(dashboard_key, metrics, alerts, queue, meta=None):
    payload = {
        'dashboard_key': str(dashboard_key),
        'metrics': list(metrics or []),
        'alerts': list(alerts or []),
        'queue': list(queue or []),
        'meta': deepcopy(meta or {}),
    }
    validate_dashboard_payload(payload)
    return payload


def validate_dashboard_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError('Dashboard payload must be a dictionary.')

    required_keys = {'dashboard_key', 'metrics', 'alerts', 'queue', 'meta'}
    missing = required_keys.difference(payload.keys())
    if missing:
        raise ValueError(f'Dashboard payload missing keys: {sorted(missing)}')

    if not isinstance(payload['dashboard_key'], str) or not payload['dashboard_key']:
        raise ValueError('dashboard_key must be a non-empty string.')

    if not isinstance(payload['metrics'], list):
        raise ValueError('metrics must be a list.')

    if not isinstance(payload['alerts'], list):
        raise ValueError('alerts must be a list.')

    if not isinstance(payload['queue'], list):
        raise ValueError('queue must be a list.')

    if not isinstance(payload['meta'], dict):
        raise ValueError('meta must be a dict.')

    for item in payload['metrics']:
        if not isinstance(item, dict):
            raise ValueError('Each metric must be an object.')
        if 'label' not in item or 'value' not in item:
            raise ValueError('Each metric must include label and value.')

    for item in payload['alerts']:
        if not isinstance(item, dict):
            raise ValueError('Each alert must be an object.')
        if 'title' not in item or 'level' not in item:
            raise ValueError('Each alert must include title and level.')

    for item in payload['queue']:
        if not isinstance(item, str):
            raise ValueError('Each queue item must be a string.')

    return True
