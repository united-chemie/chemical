from __future__ import unicode_literals
from frappe import _

def get_data(data):
    data["non_standard_fieldnames"].update({
        'Outward Sample': 'party',
        'Inward Sample': 'party'        
    })
    data['transactions'] += [
        {
            'label': _('Inward Sample'),
            'items': ['Inward Sample']
        },
        {
            'label': _('Outward Sample'),
            'items': ['Outward Sample']
        },
	]
    return data