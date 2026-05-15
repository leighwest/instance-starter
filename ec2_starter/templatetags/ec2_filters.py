from django import template

register = template.Library()


@register.filter
def status_class(value):
    status_classes = {
        'running': 'status-running',
        'stopped': 'status-stopped',
        'pending': 'status-pending',
        'stopping': 'status-stopping'
    }
    if value is None:
        return 'status-unknown'
    return status_classes.get(value.lower(), 'status-unknown')

@register.filter
def pretty_name(value):
    if value is None:
        return ''
    return value.replace('-', ' ').title()