from frappe import _


def get_data(data):
	# data['heatmap'] = True
	# data['heatmap_message'] = _('This is based on transactions against this Customer. See timeline below for details')
	# data['fieldname'] = 'customer'
	data['non_standard_fieldnames']['Inward Sample'] = 'party'
	data['non_standard_fieldnames']['Outward Sample'] = 'party'
	# data['dynamic_links'] = {
	# 	'party_name': ['Customer', 'quotation_to']
	# },
	data['transactions'] += [
		 {
			'label': _('Sample'),
			'items': ['Outward Sample','Inward Sample']
		}
	]
	return data