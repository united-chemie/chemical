from frappe import _

def get_data(data):
    data['fieldname'] = 'stock_entry'
    data['transactions'] = [
        {
            'label': _('Ball Mill Data Sheet'),
            'items': ['Ball Mill Data Sheet']
        },
    ]
    return data
    