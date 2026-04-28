from __future__ import unicode_literals
from frappe import _

def get_data(data):
    data['field_name'] = "prevdoc_docname"
    data['internal_links'] = {'Outward Sample': ['items', 'outward_sample']}
    data['transactions'] = [
        {
            'label': _('Sales Order'),
            'items': ['Sales Order']
        },
        {
            'label': _('Outward Sample'),
            'items': ['Outward Sample']
        },
	]
    return data