import frappe
from frappe import msgprint, _
from frappe.utils import flt
from frappe.utils.background_jobs import enqueue
from erpnext.stock.get_item_details import get_price_list_rate
from erpnext.manufacturing.doctype.bom.bom import get_valuation_rate
from chemical.chemical.doc_events.bom import _update_bom_cost

# override whitelisted method on hooks
@frappe.whitelist()
def enqueue_update_cost():
	frappe.msgprint(_("Queued for updating latest price in all Bill of Materials. It may take a few minutes..."))
	frappe.enqueue("chemical.chemical.whitelisted_method.bom.update_cost")

def update_cost():
	from erpnext.manufacturing.doctype.bom.bom import get_boms_in_bottom_up_order

	bom_list = get_boms_in_bottom_up_order()
	for bom in bom_list:
		bom_obj = frappe.get_doc("BOM", bom)
		bom_obj.update_cost(update_parent=False, from_child_bom=True)
		for row in bom_obj.items:
			row.db_set('per_unit_rate', flt(row.amount)/bom_obj.quantity)
		for row in bom_obj.scrap_items:
			row.db_set('per_unit_rate', flt(row.amount)/bom_obj.quantity)
		
		update_bom_cost(bom,update_parent=True, from_child_bom=False, save=True)
			

		if bom_obj.is_multiple_item:
			for item in bom_obj.multiple_finish_item:
				if bom_obj.item == item.item_code:
					bom_obj.db_set('per_unit_rmc',flt(flt(bom_obj.raw_material_cost * item.qty_ratio / 100)/bom_obj.quantity))
		else:
			bom_obj.db_set('per_unit_rmc',flt(flt(bom_obj.raw_material_cost)/bom_obj.quantity))
		
		bom_obj.db_set("volume_amount",flt(bom_obj.volume_quantity) * flt(bom_obj.volume_rate))
		volume_amount = flt(bom_obj.volume_quantity) * flt(bom_obj.volume_rate)
		bom_obj.db_set("etp_amount",flt(bom_obj.etp_qty) * flt(bom_obj.etp_rate))
		etp_amount = flt(bom_obj.etp_qty) * flt(bom_obj.etp_rate)

		bom_obj.db_set('total_operational_cost',flt(bom_obj.additional_amount) + flt(volume_amount) + flt(etp_amount))
		total_operational_cost = flt(bom_obj.additional_amount) + flt(volume_amount) + flt(etp_amount)
		bom_obj.db_set('total_scrap_cost', flt(bom_obj.scrap_material_cost))
		total_scrap_cost = flt(bom_obj.scrap_material_cost)
		bom_obj.db_set("total_cost",bom_obj.raw_material_cost + total_operational_cost - flt(bom_obj.scrap_material_cost) )
		if hasattr(bom_obj, 'total_valuation_cost'):
			bom_obj.db_set("total_valuation_cost",bom_obj.rmc_valuation_amount + total_operational_cost - flt(bom_obj.scrap_material_cost) )
			bom_obj.db_set("total_last_purchase_cost",bom_obj.rmc_last_purchase_amount + total_operational_cost - flt(bom_obj.scrap_material_cost) )
			
		per_unit_price = flt(bom_obj.total_cost) / flt(bom_obj.quantity)
		bom_obj.db_set('per_unit_price',flt(bom_obj.total_cost) / flt(bom_obj.quantity))
		bom_obj.db_set('per_unit_volume_cost',flt(volume_amount/bom_obj.quantity))	
		bom_obj.db_set('per_unit_additional_cost',flt(flt(bom_obj.additional_amount)/bom_obj.quantity))
		bom_obj.db_set('per_unit_rmc',flt(flt(bom_obj.raw_material_cost)/bom_obj.quantity))
		
		if hasattr(bom_obj, 'per_unit_rmc_valuation'):
			bom_obj.db_set('per_unit_rmc_valuation',flt(flt(bom_obj.rmc_valuation_amount)/bom_obj.quantity))
			bom_obj.db_set('per_unit_rmc_last_purchase',flt(flt(bom_obj.rmc_last_purchase_amount)/bom_obj.quantity))
			
		bom_obj.db_set('per_unit_operational_cost',flt(flt(total_operational_cost)/bom_obj.quantity))
		bom_obj.db_set('per_unit_scrap_cost',flt(flt(total_scrap_cost)/bom_obj.quantity))
		bom_obj.db_update()
		
		if bom_obj.is_default:
			if frappe.db.exists("Item Price",{"item_code":bom_obj.item,"price_list":bom_obj.buying_price_list}):
				name = frappe.db.get_value("Item Price",{"item_code":bom_obj.item,"price_list":bom_obj.buying_price_list},'name')
				item_doc = frappe.get_doc("Item Price",name)
				item_doc.db_set("price_list_rate",per_unit_price)
				item_doc.db_update()
			else:
				item_price = frappe.new_doc("Item Price")
				item_price.price_list = bom_obj.buying_price_list
				item_price.item_code = bom_obj.item
				item_price.price_list_rate = per_unit_price
			
				item_price.save()
	

# update price in BOM
# call it in bom.js
@frappe.whitelist()
def upadte_item_price(docname,item, price_list, per_unit_price):
	doc = frappe.get_doc("BOM",docname)
	for row in doc.items:
		row.db_set('per_unit_rate', flt(row.amount)/doc.quantity)
	for row in doc.scrap_items:
		row.db_set('per_unit_rate', flt(row.amount)/doc.quantity)
	
	if doc.is_multiple_item:
		for item in doc.multiple_finish_item:
			if doc.item == item.item_code:
				doc.db_set('per_unit_rmc',flt(flt(doc.raw_material_cost * item.qty_ratio / 100)/doc.quantity))
	else:
		doc.db_set('per_unit_rmc',flt(flt(doc.raw_material_cost)/doc.quantity))

	doc.db_set('volume_amount',flt(doc.volume_quantity) * flt(doc.volume_rate))
	volume_amount = flt(doc.volume_quantity) * flt(doc.volume_rate)
	doc.db_set('etp_amount',flt(doc.etp_qty) * flt(doc.etp_rate))
	etp_amount = flt(doc.etp_qty) * flt(doc.etp_rate)

	doc.db_set('total_operational_cost',flt(doc.additional_amount) + flt(volume_amount) + flt(etp_amount))
	total_operational_cost = flt(doc.additional_amount) + flt(volume_amount) + flt(etp_amount)
	doc.db_set('total_scrap_cost', flt(doc.scrap_material_cost))
	total_scrap_cost = flt(doc.scrap_material_cost)

	doc.db_set("total_cost",doc.raw_material_cost + flt(total_operational_cost) - flt(doc.scrap_material_cost))
	total_cost = doc.raw_material_cost + flt(total_operational_cost) - flt(doc.scrap_material_cost)

	if hasattr(doc, 'total_valuation_cost'):
		doc.db_set("total_valuation_cost",doc.rmc_valuation_amount + flt(total_operational_cost) - flt(doc.scrap_material_cost))
		total_valuation_cost = doc.rmc_valuation_amount + flt(total_operational_cost) - flt(doc.scrap_material_cost)
		doc.db_set("total_last_purchase_cost",doc.rmc_last_purchase_amount + flt(total_operational_cost) - flt(doc.scrap_material_cost))
		total_last_purchase_cost = doc.rmc_last_purchase_amount + flt(total_operational_cost) - flt(doc.scrap_material_cost)

	doc.db_set('per_unit_price',flt(doc.total_cost) / flt(doc.quantity))
	if hasattr(doc, 'per_unit_valuation_price'):
		doc.db_set('per_unit_valuation_price',flt(total_valuation_cost) / flt(doc.quantity))
		doc.db_set('per_unit_last_purchase_price',flt(total_last_purchase_cost) / flt(doc.quantity))
		
	
	doc.db_set('per_unit_rmc',flt(flt(doc.raw_material_cost)/doc.quantity))
	if hasattr(doc, 'per_unit_rmc_valuation'):
		doc.db_set('per_unit_rmc_valuation',flt(flt(doc.rmc_valuation_amount)/doc.quantity))
		doc.db_set('per_unit_rmc_last_purchase',flt(flt(doc.rmc_last_purchase_amount)/doc.quantity))
		
	doc.db_set('per_unit_volume_cost',flt(volume_amount/doc.quantity))	
	doc.db_set('per_unit_additional_cost',flt(flt(doc.additional_amount)/doc.quantity))
	doc.db_set('per_unit_operational_cost',flt(flt(total_operational_cost)/doc.quantity))
	doc.db_set('per_unit_scrap_cost',flt(flt(total_scrap_cost)/doc.quantity))
	doc.db_update()


	if doc.is_default:
		if frappe.db.exists("Item Price",{"item_code":item,"price_list":price_list}):
			name = frappe.db.get_value("Item Price",{"item_code":item,"price_list":price_list},'name')
			# frappe.db.set_value("Item Price",name,"price_list_rate", per_unit_price)
			item_doc = frappe.get_doc("Item Price",name)
			item_doc.db_set("price_list_rate",per_unit_price)
			item_doc.db_update()
		else:
			item_price = frappe.new_doc("Item Price")
			item_price.price_list = price_list
			item_price.item_code = item
			item_price.price_list_rate = per_unit_price
			
			item_price.save()
		
		return "Item Price Updated!"
	
@frappe.whitelist()	
def update_bom_cost(doc,update_parent=True, from_child_bom=False, save=True):
	bom_doc = frappe.get_doc("BOM",doc)
	if bom_doc.rm_cost_as_per != "Valuation Rate":
		_update_bom_cost(bom_doc,update_parent=update_parent, from_child_bom=from_child_bom, save=save)
	else:
		from erpnext.manufacturing.doctype.bom.bom import BOM
		BOM.update_cost(bom_doc,update_parent=update_parent, from_child_bom=from_child_bom, save=save)

@frappe.whitelist()	
def update_item_price_daily():
	data = frappe.db.sql("""
		select 
			item, per_unit_price , buying_price_list
		from
			`tabBOM` 
		where 
			docstatus < 2 
			and is_default = 1 """,as_dict =1)
			
	for row in data:
		update_item_price(row.item, row.buying_price_list, row.per_unit_price)
		
	return "Latest price updated in Price List."

@frappe.whitelist()
def update_item_price(item, price_list, per_unit_price):
	
	if frappe.db.exists("Item Price",{"item_code":item,"price_list":price_list}):
		name = frappe.db.get_value("Item Price",{"item_code":item,"price_list":price_list},'name')
		frappe.db.set_value("Item Price",name,"price_list_rate", per_unit_price)	
	else:
		item_price = frappe.new_doc("Item Price")
		item_price.price_list = price_list
		item_price.item_code = item
		item_price.price_list_rate = per_unit_price
	
		item_price.save()
	frappe.db.commit()
		
	return ["Item Price Updated!",per_unit_price]
