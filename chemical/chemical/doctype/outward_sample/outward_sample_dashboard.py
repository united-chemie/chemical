from frappe import _

def get_data():
	return {
		'fieldname': 'outward_sample',
		'non_standard_fieldnames': {
			'Quality Inspection': 'reference_name',
			'Quotation': 'outward_sample'
		},
		'transactions': [
			{	
				'label': _('Quality Inspection'),
				'items': ['Quality Inspection']
			},
				{	
				'label': _('Quotation'),
				'items': ['Quotation']
			},
		]
	}