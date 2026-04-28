import frappe
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from chemical.api import se_cal_rate_qty, se_repack_cal_rate_qty, cal_actual_valuations
from six import iteritems
from frappe import msgprint, _
# from chemical.batch_valuation import set_incoming_rate

class FinishedGoodError(frappe.ValidationError):
	pass

def onload(self,method):
	pass
	#quantity_price_to_qty_rate(self)

def stock_entry_after_submit(self, method):
	pass
	# set_batch_qc(self)

def before_validate(self,method):
	update_item_batches_based_on_fifo(self)
	for idx, item in enumerate(self.items):
		item.idx = idx + 1
	if self.purpose in ['Material Receipt','Repack'] and hasattr(self,'party_type') and hasattr(self,'reference_docname') and hasattr(self,'jw_ref'):
		if not self.reference_docname and not self.jw_ref and self.party_type == "Supplier":
			se_repack_cal_rate_qty(self)
		else:
			se_cal_rate_qty(self)
	else:
		se_cal_rate_qty(self)
	fg_completed_quantity_to_fg_completed_qty(self)
	cal_actual_valuations(self)
	validate_fg_completed_quantity(self)

def validate(self,method):
	if self.purpose in ['Manufacture']:
		item_list = [item.item_code for item in self.items]
		if self.based_on not in item_list:
			frappe.throw("Based on Item {} Required in Raw Materials".format(frappe.bold(self.based_on)))	
	cal_validate_additional_cost_qty(self)
	# update_additional_cost_scrap(self)
	calculate_rate_and_amount(self)
	get_based_on(self)
	cal_target_yield_cons(self)
	# if self.additional_costs:
	# 	self.total_additional_costs = sum([flt(t.amount) for t in self.get("additional_costs")])

def stock_entry_validate(self, method):
	if self.purpose == "Material Receipt":
		validate_batch_wise_item_for_concentration(self)
	#update_additional_cost(self)

def stock_entry_before_save(self, method):
	if self.purpose == 'Repack' and cint(self.from_ball_mill) != 1:
		self.get_stock_and_rate()

def before_submit(self, method):
	if self.purpose == "Manufacture" and self.bom_no:
		if frappe.db.get_value("BOM",self.bom_no,"inspection_required")==1:
			for row in self.items:
				if row.t_warehouse and not row.quality_inspection:
					frappe.throw(_("Quality Inspection is mandatory in row {0} for item {1}.".format(row.idx,row.item_code)))
	validate_concentration(self)

def se_before_submit(self, method):
	validate_concentration(self)

def on_submit(self, method):
	update_Wo(self)
	set_batch_qc(self)

def se_before_cancel(self, method):
	StockEntry.delete_auto_created_batches = delete_auto_created_batches
	if self.work_order:
		wo = frappe.get_doc("Work Order",self.work_order)
		wo.db_set('batch','')

def on_cancel(self,method):	
	update_work_order_on_cancel(self,method)

	for item in self.items:
		if item.t_warehouse:
			item.batch_no = None
			item.db_set("batch_no",None)

	for data in frappe.get_all("Batch",{'reference_name': self.name, 'reference_doctype': self.doctype}):
		frappe.db.set_value('Batch',data.name,'reference_name','')
		#frappe.delete_doc("Batch", data.name)

def stock_entry_on_cancel(self, method):
	if self.work_order:
		pro_doc = frappe.get_doc("Work Order", self.work_order)
		set_po_status(self, pro_doc)			
		#pro_doc.save()
		#frappe.db.commit()

def quantity_price_to_qty_rate(self):
	for item in self.items:
		if item.qty and item.quantity == 0:
			item.db_set("quantity",flt(item.qty))
		if item.basic_rate and item.price ==0:
			item.db_set("price",flt(item.basic_rate))

def validate_fg_completed_quantity(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		if self.purpose == "Manufacture" and self.work_order:
			#production_item = frappe.get_value('Work Order', self.work_order, 'production_item')
			fg_qty = 0.0
			fg_quantity = 0.0	
			for item in self.items:
				if item.t_warehouse and item.is_finished_item:
					fg_qty += item.qty
					fg_quantity += item.quantity
			self.fg_completed_qty = round(fg_qty,3)
			self.fg_completed_quantity = fg_quantity
			# if fg_quantity != self.fg_completed_quantity:
			# 	frappe.throw(_("Finished product quantity <b>{0}</b> and For Quantity <b>{1}</b> cannot be different")
			# 			.format(fg_quantity, self.fg_completed_quantity))	
	else:
		pass
	
def get_based_on(self):
	if self.work_order:
		self.based_on = frappe.db.get_value("Work Order", self.work_order, 'based_on')


# def update_additional_cost_scrap(self):
# 	if self.purpose == "Manufacture" and self.bom_no:
# 		bom_qty = 1
# 		se_qty = 1
# 		bom = frappe.get_doc("BOM",self.bom_no)
# 		for m in self.items:
# 			if m.item_code == bom.based_on:
# 				se_qty = m.qty
# 				break

# 		for row in bom.items:
# 			if row.item_code == bom.based_on:
# 				bom_qty = row.qty
# 				break

# 		amount = 0
# 		if bom.scrap_items:
# 			if self.is_new() and not self.amended_from:
# 				for d in bom.scrap_items:
# 					self.append('additional_costs', {
# 						'description': d.item_code,
# 						'qty': flt(flt(se_qty * d.stock_qty)/ bom_qty),
# 						'rate': abs(d.rate),
# 						'amount':  abs(d.rate)* flt(flt(se_qty * d.stock_qty)/ bom_qty),
# 						'base_amount':abs(d.rate)* flt(flt(se_qty * d.stock_qty)/ bom_qty)
# 					})
# 			else:
# 				for d in bom.scrap_items:
# 					for i in self.additional_costs:
# 						if i.description == d.item_code:
# 							i.qty = flt(flt(se_qty * d.stock_qty)/ row.qty)
# 							i.rate = abs(d.rate)
# 							i.amount = abs(d.rate)* flt(flt(se_qty * d.stock_qty)/ row.qty)  
# 							i.base_amount = abs(d.rate)* flt(flt(se_qty * d.stock_qty)/ row.qty) 
# 							break

def sum_total_additional_costs(self):
	self.total_additional_costs = sum(m.amount for m in self.additional_costs)

def calculate_rate_and_amount(self, reset_outgoing_rate=True, raise_error_if_no_rate=True):
	# if self.purpose in ["Material Transfer for Manufacture"]:
	# 	set_incoming_rate(self)
	if self.purpose in ['Manufacture','Repack']:
		is_multiple_finish  = 0
		multi_item_list = []
		for d in self.items:
			if d.t_warehouse and d.qty != 0 and d.is_finished_item:
				is_multiple_finish +=1
				multi_item_list.append(d.item_code)
		if is_multiple_finish > 1 and self.purpose == "Manufacture":
			self.set_basic_rate(reset_outgoing_rate=False, raise_error_if_no_rate=True)
			bom_doc = frappe.get_doc("BOM",self.bom_no)
			if hasattr(bom_doc,'equal_cost_ratio'):
				if not bom_doc.equal_cost_ratio:
					cal_rate_for_finished_item(self)
				# elif len(list(set(multi_item_list))) == 1 and bom_doc.equal_cost_ratio:
				# 	calculate_multiple_repack_valuation(self)
				else:
					calculate_multiple_repack_valuation(self)
			else:
				cal_rate_for_finished_item(self)

		elif is_multiple_finish > 1 and self.purpose == "Repack":
			self.set_basic_rate(reset_outgoing_rate=False, raise_error_if_no_rate=True)
			calculate_multiple_repack_valuation(self)
		
		else:
			self.set_basic_rate(reset_outgoing_rate=True, raise_error_if_no_rate=True)
			self.distribute_additional_costs()

	else:
		self.set_basic_rate(reset_outgoing_rate=True, raise_error_if_no_rate=True)
		self.distribute_additional_costs()
	self.update_valuation_rate()
	# Finbyz Changes start: Calculate Valuation Price Based on Valuation Rate and concentration for AS IS Items 
	# update_valuation_price(self)
	# Finbyz Changes End
	self.set_total_incoming_outgoing_value()
	self.set_total_amount()
	price_to_rate(self)

def price_to_rate(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		for item in self.items:
			has_batch_no,maintain_as_is_stock = frappe.db.get_value('Item', item.item_code, ['has_batch_no','maintain_as_is_stock'])
			concentration = item.concentration or 100	
			if item.basic_rate:
				if maintain_as_is_stock:
					item.price = flt(item.basic_rate)*100/concentration
				else:
					item.price = flt(item.basic_rate)	
	
def cal_target_yield_cons(self):
	cal_yield = 0
	cons = 0
	tot_quan = 0
	item_arr = list()
	item_map = dict()
	flag = 0
	if self.purpose == "Manufacture" and self.based_on:
		if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
			for d in self.items:
				if d.t_warehouse:
					flag+=1		
				
				if d.item_code not in item_arr:
						item_map.setdefault(d.item_code, {'quantity':0, 'qty':0, 'yield_weights':0})
					
				item_map[d.item_code]['quantity'] += flt(d.quantity)
				item_map[d.item_code]['qty'] += flt(d.qty)
				item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.quantity)

			if flag == 1:
				# Last row object
				last_row = self.items[-1]

				# Last row batch_yield
				batch_yield = last_row.batch_yield

				# List of item_code from items table
				items_list = [row.item_code for row in self.items]

				# Check if items list has frm.doc.based_on value
				if self.based_on in items_list:
					# item_yield = 0.0
					# if item_map[self.based_on]['yield_weights'] > 0:
					# 	item_yield = item_map[self.based_on]['yield_weights'] / item_map[self.based_on]['quantity']

					# 	if item_yield:
					# 		cal_yield = flt(item_yield) * flt(last_row.qty / item_map[self.based_on]['quantity']) # Last row qty / sum of items of based_on item from map variable
					# 	else:
					cal_yield =  flt(last_row.qty / item_map[self.based_on]['quantity'])
				# last_row.batch_yield = flt(cal_yield) * (flt(last_row.concentration) / 100.0)
		else:
			for d in self.items:
				if d.t_warehouse:
					flag+=1		
				
				if d.item_code not in item_arr:
						item_map.setdefault(d.item_code, {'qty':0, 'yield_weights':0})
					
				# item_map[d.item_code]['quantity'] += flt(d.quantity)
				item_map[d.item_code]['qty'] += flt(d.qty)
				item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.qty)

			if flag == 1:
				# Last row object
				last_row = self.items[-1]

				# Last row batch_yield
				batch_yield = last_row.batch_yield

				# List of item_code from items table
				items_list = [row.item_code for row in self.items]

				# Check if items list has frm.doc.based_on value
				if self.based_on in items_list:
					# item_yield = 0.0
					# if item_map[self.based_on]['yield_weights'] > 0:
					# 	item_yield = item_map[self.based_on]['yield_weights'] / item_map[self.based_on]['quantity']

					# 	if item_yield:
					# 		cal_yield = flt(item_yield) * flt(last_row.qty / item_map[self.based_on]['quantity']) # Last row qty / sum of items of based_on item from map variable
					# 	else:
					cal_yield =  flt(last_row.qty / item_map[self.based_on]['qty'])
				last_row.batch_yield = flt(cal_yield)

def cal_validate_additional_cost_qty(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		if self.additional_costs:
			for addi_cost in self.additional_costs:
				if addi_cost.qty and addi_cost.rate:
					addi_cost.amount = flt(addi_cost.qty) * flt(addi_cost.rate)
					addi_cost.base_amount = flt(addi_cost.qty) * flt(addi_cost.rate)
				if addi_cost.uom == "FG QTY":
					addi_cost.qty = self.fg_completed_quantity
					addi_cost.amount = flt(self.fg_completed_quantity) * flt(addi_cost.rate)
					addi_cost.base_amount = flt(self.fg_completed_quantity) * flt(addi_cost.rate)
	else:
		if self.additional_costs:
			for addi_cost in self.additional_costs:
				if addi_cost.qty and addi_cost.rate:
					addi_cost.amount = flt(addi_cost.qty) * flt(addi_cost.rate)
					addi_cost.base_amount = flt(addi_cost.qty) * flt(addi_cost.rate)
				if addi_cost.uom == "FG QTY":
					addi_cost.qty = self.fg_completed_qty
					addi_cost.amount = flt(self.fg_completed_qty) * flt(addi_cost.rate)
					addi_cost.base_amount = flt(self.fg_completed_qty) * flt(addi_cost.rate)

def fg_completed_quantity_to_fg_completed_qty(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		if self.fg_completed_qty == 0:
			self.fg_completed_qty = self.fg_completed_quantity
	
def validate_concentration(self):
	if self.work_order and self.purpose == "Manufacture":
		wo_item = frappe.db.get_value("Work Order",self.work_order,'production_item')
		for row in self.items:
			if row.t_warehouse and row.item_code == wo_item and not row.concentration:
				frappe.throw(_("Add concentration in row {} for item {}".format(row.idx,row.item_code)))

def update_Wo(self):
	if self.work_order:
		po = frappe.get_doc("Work Order", self.work_order)
		if self.purpose == "Material Transfer for Manufacture":
			if po.material_transferred_for_manufacturing > po.qty:
				po.material_transferred_for_manufacturing = po.qty
			
			# if not frappe.db.exists({"doctype":"Stock Entry","name":("!=",self.name),"stock_entry_type":"Material Transfer for Manufacture","work_order":self.work_order}):
			if not frappe.db.sql("""select name from `tabStock Entry` where name != '{}' and stock_entry_type = 'Material Transfer for Manufacture' and work_order = '{}'""".format(self.name,self.work_order)):
				po.db_set('actual_start_date',self.posting_date + ' ' +  self.posting_time)
		if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
			if self.purpose == "Manufacture" and self.work_order:
				update_po_items(self, po)

				# update finised item detail
				count = 0
				batch_yield = 0.0
				concentration = 0.0
				total_qty = 0.0
				actual_total_qty = 0.0
				valuation_rate = 0.0
				lot = []
				finished_item = {}
				finished_item_list = []
				s = ', '
				
				po.finish_item = []
				if po.bom_no:
					bom_doc = frappe.get_doc("BOM",po.bom_no)
				# po.append("finish_item",finished_item_list)
				finish_items_length= [item.idx for item in self.items if item.t_warehouse]		
				for row in self.items:
					if row.t_warehouse:
						count += 1
						batch_yield += row.batch_yield
						concentration += row.concentration
						total_qty += row.qty
						# actual_total_qty += row.quantity
						valuation_rate += flt(row.qty)*flt(row.valuation_rate)
						if row.lot_no:
							lot.append(row.lot_no)
						if bom_doc.multiple_finish_item:
							for bom_fi in bom_doc.multiple_finish_item:
								if bom_fi.item_code == row.item_code:
									po.append("finish_item",{
										'item_code': row.item_code,
										'actual_qty': row.qty,
										'actual_valuation': row.valuation_rate,
										'lot_no': row.lot_no,
										'purity': row.concentration,
										'packing_size': row.packing_size,
										'no_of_packages': row.no_of_packages,
										'batch_yield': row.batch_yield,
										'batch_no': row.batch_no,
										"bom_cost_ratio":bom_fi.cost_ratio,
										"bom_qty_ratio":bom_fi.qty_ratio,
										"bom_qty":po.qty * bom_fi.qty_ratio / 100,
										"bom_yield":bom_fi.batch_yield
									})
						else:
							po.append("finish_item",{
								'item_code': row.item_code,
								'actual_qty': row.qty,
								'actual_valuation': row.valuation_rate,
								'lot_no': row.lot_no,
								'purity': row.concentration,
								'packing_size': row.packing_size,
								'no_of_packages': row.no_of_packages,
								'batch_yield': row.batch_yield,
								'batch_no': row.batch_no,
								"bom_cost_ratio":100,
								"bom_qty_ratio":100,
								"bom_qty": po.qty,
								"bom_yield": bom_doc.batch_yield
							})
				
				for child in po.finish_item:
					child.db_update()
				po.db_set("batch_yield", flt(batch_yield))
				po.db_set("concentration", flt(concentration))
				po.db_set("valuation_rate", valuation_rate / flt(actual_total_qty))
				po.db_set("produced_qty", total_qty)
				po.db_set('valuation_price',(((flt(valuation_rate) / flt(actual_total_qty)) * total_qty) / actual_total_qty))
				
				
				if len(lot)!=0:
					po.db_set("lot_no", s.join(lot))
		else:
			if self.purpose == "Manufacture" and self.work_order:
				update_po_items(self, po)

				# update finised item detail
				count = 0
				batch_yield = 0.0
				concentration = 0.0
				total_qty = 0.0
				actual_total_qty = 0.0
				valuation_rate = 0.0
				lot = []
				finished_item = {}
				finished_item_list = []
				s = ', '
				
				po.finish_item = []
				if po.bom_no:
					bom_doc = frappe.get_doc("BOM",po.bom_no)
				# po.append("finish_item",finished_item_list)
				finish_items_length= [item.idx for item in self.items if item.t_warehouse]		
				for row in self.items:
					if row.t_warehouse:
						count += 1
						batch_yield += row.batch_yield
						concentration += row.concentration
						total_qty += row.qty
						# actual_total_qty += row.quantity
						valuation_rate += flt(row.qty)*flt(row.valuation_rate)
						if row.lot_no:
							lot.append(row.lot_no)
						if bom_doc.multiple_finish_item:
							for bom_fi in bom_doc.multiple_finish_item:
								if bom_fi.item_code == row.item_code:
									po.append("finish_item",{
										'item_code': row.item_code,
										'actual_qty': row.qty,
										'actual_valuation': row.valuation_rate,
										'lot_no': row.lot_no,
										'purity': row.concentration,
										'packing_size': row.packing_size,
										'no_of_packages': row.no_of_packages,
										'batch_yield': row.batch_yield,
										'batch_no': row.batch_no,
										"bom_cost_ratio":bom_fi.cost_ratio,
										"bom_qty_ratio":bom_fi.qty_ratio,
										"bom_qty":po.qty * bom_fi.qty_ratio / 100,
										"bom_yield":bom_fi.batch_yield
									})
						else:
							po.append("finish_item",{
								'item_code': row.item_code,
								'actual_qty': row.qty,
								'actual_valuation': row.valuation_rate,
								'lot_no': row.lot_no,
								'purity': row.concentration,
								'packing_size': row.packing_size,
								'no_of_packages': row.no_of_packages,
								'batch_yield': row.batch_yield,
								'batch_no': row.batch_no,
								"bom_cost_ratio":100,
								"bom_qty_ratio":100,
								"bom_qty": po.qty,
								"bom_yield": bom_doc.batch_yield
							})
				
				for child in po.finish_item:
					child.db_update()
				po.db_set("batch_yield", flt(batch_yield))
				po.db_set("concentration", flt(concentration))
				po.db_set("valuation_rate", valuation_rate / flt(total_qty))
				po.db_set("produced_qty", total_qty)
				# po.db_set("produced_quantity",total_qty)
				# valuation price = valuation_rate * produced_qty / produced_quantity
				# po.db_set('valuation_price',(((flt(valuation_rate) / flt(actual_total_qty)) * total_qty) / actual_total_qty))
				if len(lot)!=0:
					po.db_set("lot_no", s.join(lot))

def update_work_order_on_cancel(self, method):
	if self.purpose == 'Manufacture' and self.work_order:
		# doc = frappe.get_doc("Work Order",self.work_order)
		# doc.finish_item = []
		# doc.db_set('batch_yield',0)
		# doc.db_set('concentration',0)
		# doc.db_set('valuation_rate',0)
		# doc.db_set('produced_quantity',0)
		# doc.db_set('lot_no','')
		# for item in doc.finish_item:
		# 	item.db_set("actual_qty",0)
		# 	item.db_set("actual_valuation",0)
		# 	item.db_set("lot_no",'')
		# 	item.db_set("packing_size",0)
		# 	item.db_set("no_of_packages",0)
		# 	item.db_set("purity",0)
		# 	item.db_set("batch_yield",0)
		# 	item.db_set("batch_no",'')
			# item.db_update()
		frappe.db.sql("""delete from `tabWork Order Finish Item`
			where parent = %s""", self.work_order)
		
		# doc.db_update()

def set_po_status(self, pro_doc):
	status = None
	if flt(pro_doc.material_transferred_for_instruction):
		status = "In Process"

	if status:
		pro_doc.db_set('status', status)

def calculate_multiple_repack_valuation(self):
	self.total_additional_costs = sum([flt(t.amount) for t in self.get("additional_costs")])
	scrap_total = 0
	if self.items:
		qty = 0.0
		total_outgoing_value = 0.0
		
		for row in self.items:
			if row.s_warehouse:
				total_outgoing_value += flt(row.basic_amount)
			if row.t_warehouse:
				qty += row.qty
			if row.is_scrap_item:
				scrap_total += flt(row.basic_amount)
		total_outgoing_value = flt(total_outgoing_value) - flt(scrap_total)
		
		for row in self.items:
			if row.t_warehouse:
				row.basic_amount = flt(total_outgoing_value) * flt(row.qty)/ qty
				row.additional_cost = flt(self.total_additional_costs) * flt(row.qty)/ qty
				row.basic_rate =  flt(row.basic_amount/ row.qty)

def cal_rate_for_finished_item(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		self.total_additional_costs = sum([flt(t.amount) for t in self.get("additional_costs")])
		work_order = frappe.get_doc("Work Order",self.work_order)
		work_order.ignore_permissions = True
		bom_doc = frappe.get_doc("BOM",self.bom_no)
		bom_doc.ignore_permissions = True
		is_multiple_finish = 0
		scrap_total = 0
		for d in self.items:
			if d.t_warehouse and not d.is_scrap_item:
				is_multiple_finish +=1
			if d.is_scrap_item:
					scrap_total += flt(d.basic_amount)
		if self.total_outgoing_value:
			self.total_outgoing_value = max(flt(self.total_outgoing_value) - flt(scrap_total),0)
		if is_multiple_finish > 1:
			total_incoming_amount = 0.0
			item_arr = list()
			item_map = dict()
			finished_list = []
			result = {}
			cal_yield = 0
			if self.purpose == 'Manufacture' and self.bom_no:
				for row in self.items:
					if row.t_warehouse and not d.is_scrap_item:
						finished_list.append({row.item_code:row.quantity}) #create a list of dict of finished item
				for d in finished_list:
					for k in d.keys():
						result[k] = result.get(k, 0) + d[k] # create a dict of unique item 
							
				for d in self.items:
					if d.item_code not in item_arr:
						item_map.setdefault(d.item_code, {'quantity':0, 'qty':0, 'yield_weights':0})
					
					item_map[d.item_code]['quantity'] += flt(d.quantity)
					item_map[d.item_code]['qty'] += flt(d.qty)
					item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.quantity)

					bom_cost_list = []
					if bom_doc.is_multiple_item:
						for bom_fi in bom_doc.multiple_finish_item:
							bom_cost_list.append({"item_code":bom_fi.item_code,"cost_ratio":bom_fi.cost_ratio})
					else:
						bom_cost_list.append({"item_code":bom_doc.item,"cost_ratio":100})
					if d.t_warehouse:
						for bom_cost_dict in bom_cost_list:
							if d.item_code == bom_cost_dict["item_code"]:
								# d.db_set('basic_amount',flt(flt(self.total_outgoing_value*bom_cost_dict["cost_ratio"]*d.quantity)/flt(100*result[d.item_code])))
								# d.db_set('additional_cost',flt(flt(self.total_additional_costs*bom_cost_dict["cost_ratio"]*d.quantity)/flt(100*result[d.item_code])))
								# d.db_set('amount',flt(d.basic_amount + d.additional_cost))
								# d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
								# d.db_set('valuation_rate',flt(d.amount/ d.qty))
								d.basic_amount = flt(flt(flt(self.total_outgoing_value)*flt(bom_cost_dict["cost_ratio"])*flt(d.quantity))/flt(100*flt(result[d.item_code])))
								d.additional_cost = flt(flt(flt(self.total_additional_costs)*flt(bom_cost_dict["cost_ratio"])*flt(d.quantity))/flt(100*flt(result[d.item_code])))
								d.amount = flt(d.basic_amount + d.additional_cost)
								d.basic_rate = flt(d.basic_amount/ d.qty)
								d.valuation_rate = flt(d.amount/ d.qty)

								item_yield = 0.0
								if item_map[self.based_on]['yield_weights'] > 0:
									item_yield = item_map[self.based_on]['yield_weights'] / item_map[self.based_on]['quantity']

								based_on_qty_ratio = d.quantity / (self.fg_completed_quantity or self.fg_completed_qty)
								if self.based_on:
									# if item_yield:
									# 	d.batch_yield = flt((d.qty * d.concentration * item_yield) / (100*flt(item_map[self.based_on]['quantity']*finish_items.bom_qty_ratio/100)))
									# else:
									d.batch_yield = flt(d.qty / (flt(item_map[self.based_on]['quantity'])))

						# total_incoming_amount += flt(d.amount)

				# d.db_update()

						# first_item_ratio = abs(100-self.cost_ratio_of_second_item)
						# first_item_qty_ratio = abs(100-self.qty_ratio_of_second_item)
						
						# if d.item_code == frappe.db.get_value('Work Order',self.work_order,'production_item'):
						# 	d.db_set('basic_amount',flt(flt(self.total_outgoing_value*first_item_ratio*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('additional_cost',flt(flt(self.total_additional_costs*first_item_ratio*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('amount',flt(d.basic_amount + d.additional_cost))
						# 	d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
						# 	d.db_set('valuation_rate',flt(d.amount/ d.qty))

						# 	if self.based_on:
						# 		d.batch_yield = flt(result[d.item_code] / flt(item_map[self.based_on]*first_item_qty_ratio/100))
							
						# if d.item_code == self.second_item:
						# 	d.db_set('basic_amount',flt(flt(self.total_outgoing_value*self.cost_ratio_of_second_item*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('additional_cost',flt(flt(self.total_additional_costs*self.cost_ratio_of_second_item*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('amount',flt(d.basic_amount + d.additional_cost))
						# 	d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
						# 	d.db_set('valuation_rate',flt(d.amount/ d.qty))
							
						# 	if self.based_on:
						# 		d.batch_yield = flt(result[d.item_code] / flt(item_map[self.based_on]*self.qty_ratio_of_second_item/100))  # cost_ratio_of_second_item percent of sum of items of based_on item from map variable 				
	else:
		self.total_additional_costs = sum([flt(t.amount) for t in self.get("additional_costs")])
		work_order = frappe.get_doc("Work Order",self.work_order)
		work_order.ignore_permissions = True
		bom_doc = frappe.get_doc("BOM",self.bom_no)
		bom_doc.ignore_permissions = True
		is_multiple_finish = 0
		scrap_total = 0
		for d in self.items:
			if d.t_warehouse and not d.is_scrap_item:
				is_multiple_finish +=1
			if d.is_scrap_item:
				scrap_total += flt(d.basic_amount)
		if self.total_outgoing_value:
			self.total_outgoing_value = max(flt(self.total_outgoing_value) - flt(scrap_total),0)
		if is_multiple_finish > 1:
			total_incoming_amount = 0.0
			item_arr = list()
			item_map = dict()
			finished_list = []
			result = {}
			cal_yield = 0
			if self.purpose == 'Manufacture' and self.bom_no:
				for row in self.items:
					if row.t_warehouse and not d.is_scrap_item:
						finished_list.append({row.item_code:row.qty}) #create a list of dict of finished item
				for d in finished_list:
					for k in d.keys():
						result[k] = result.get(k, 0) + d[k] # create a dict of unique item 
							
				for d in self.items:
					if d.item_code not in item_arr:
						item_map.setdefault(d.item_code, {'qty':0, 'yield_weights':0})
					
					# item_map[d.item_code]['quantity'] += flt(d.quantity)
					item_map[d.item_code]['qty'] += flt(d.qty)
					# item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.quantity)

					bom_cost_list = []
					if bom_doc.is_multiple_item:
						for bom_fi in bom_doc.multiple_finish_item:
							bom_cost_list.append({"item_code":bom_fi.item_code,"cost_ratio":bom_fi.cost_ratio})
					else:
						bom_cost_list.append({"item_code":bom_doc.item,"cost_ratio":100})
					if d.t_warehouse:
						for bom_cost_dict in bom_cost_list:
							if d.item_code == bom_cost_dict["item_code"]:
								d.basic_amount = flt(flt(flt(self.total_outgoing_value)*flt(bom_cost_dict["cost_ratio"])*flt(d.qty))/flt(100*flt(result[d.item_code])))
								d.additional_cost = flt(flt(flt(self.total_additional_costs)*flt(bom_cost_dict["cost_ratio"])*flt(d.qty))/flt(100*flt(result[d.item_code])))
								d.amount = flt(d.basic_amount + d.additional_cost)
								d.basic_rate = flt(d.basic_amount/ d.qty)
								d.valuation_rate = flt(d.amount/ d.qty)

								# if self.based_on:
								# 	# if item_yield:
								# 	# 	d.batch_yield = flt((d.qty * d.concentration * item_yield) / (100*flt(item_map[self.based_on]['quantity']*finish_items.bom_qty_ratio/100)))
								# 	# else:
								# 	d.batch_yield = flt((d.qty * d.concentration) / (100*flt(item_map[self.based_on]['qty']*flt(based_on_qty_ratio)/100)))

						# total_incoming_amount += flt(d.amount)

				# d.db_update()

						# first_item_ratio = abs(100-self.cost_ratio_of_second_item)
						# first_item_qty_ratio = abs(100-self.qty_ratio_of_second_item)
						
						# if d.item_code == frappe.db.get_value('Work Order',self.work_order,'production_item'):
						# 	d.db_set('basic_amount',flt(flt(self.total_outgoing_value*first_item_ratio*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('additional_cost',flt(flt(self.total_additional_costs*first_item_ratio*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('amount',flt(d.basic_amount + d.additional_cost))
						# 	d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
						# 	d.db_set('valuation_rate',flt(d.amount/ d.qty))

						# 	if self.based_on:
						# 		d.batch_yield = flt(result[d.item_code] / flt(item_map[self.based_on]*first_item_qty_ratio/100))
							
						# if d.item_code == self.second_item:
						# 	d.db_set('basic_amount',flt(flt(self.total_outgoing_value*self.cost_ratio_of_second_item*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('additional_cost',flt(flt(self.total_additional_costs*self.cost_ratio_of_second_item*d.quantity)/flt(100*result[d.item_code])))
						# 	d.db_set('amount',flt(d.basic_amount + d.additional_cost))
						# 	d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
						# 	d.db_set('valuation_rate',flt(d.amount/ d.qty))
							
						# 	if self.based_on:
						# 		d.batch_yield = flt(result[d.item_code] / flt(item_map[self.based_on]*self.qty_ratio_of_second_item/100))  # cost_ratio_of_second_item percent of sum of items of based_on item from map variable 				


def update_valuation_price(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		for item in self.items:
			maintain_as_is_stock = frappe.db.get_value('Item', item.item_code, 'maintain_as_is_stock')
			concentration = item.concentration or 100
			if maintain_as_is_stock:
				item.valuation_price = flt(item.valuation_rate) * 100 / flt(concentration)
			else:
				item.valuation_price = flt(item.valuation_rate)
	else:
		pass

def update_additional_cost(self):
	if self.purpose == "Manufacture" and self.bom_no:
		bom = frappe.get_doc("BOM",self.bom_no)
		abbr = frappe.db.get_value("Company",self.company,'abbr')
		
		if self.is_new() and not self.amended_from:
			if bom.additional_cost:
				for d in bom.additional_cost:
					self.append('additional_costs', {
						'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
						'description': d.description,
						'qty': flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity),
						'rate': abs(d.rate),
						'amount':  abs(d.rate)* flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity),
						'base_amount':  abs(d.rate)* flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
					})
		else:
			for row in self.additional_costs:
				if bom.additional_cost:
					for d in bom.additional_cost:
						if row.description == d.description:
							row.rate = abs(d.rate)
							row.qty = flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
							if row.rate and row.qty:
								row.amount = abs(d.rate)* flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
								row.base_amount = abs(d.rate)* flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
		self.db_set('total_additional_costs',sum([row.amount for row in self.additional_costs]))

def validate_lot(self):
	for row in self.items:
		if row.t_warehouse and not row.s_warehouse:
			if not row.lot_no:
				frappe.throw(_("Add lot_no in row {} for item {}".format(row.idx,row.item_code)))
	
def validate_batch_wise_item_for_concentration(self):
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

		# if not has_batch_no and flt(row.concentration):
			# frappe.throw(_("Row #{idx}. Please remove concentration for non batch item {item_code}.".format(idx = row.idx, item_code = frappe.bold(row.item_code))))
		if not has_batch_no:
			row.concentration = 100

def update_po_items(self,po):
	from erpnext.stock.utils import get_latest_stock_qty

	for row in self.items:
		if row.s_warehouse and not row.t_warehouse:
			item = [d.name for d in po.required_items if d.item_code == row.item_code]

			if not item:
				po.append('required_items', {
					'item_code': row.item_code,
					'item_name': row.item_name,
					'description': row.description,
					'source_warehouse': row.s_warehouse,
					'required_qty': row.qty,
					'transferred_qty': row.quantity,
					'valuation_rate': row.valuation_rate,
					'available_qty_at_source_warehouse': get_latest_stock_qty(row.item_code, row.s_warehouse),
				})

	for child in po.required_items:
		child.db_update()

def validate_finished_goods(self):
	"""validation: finished good quantity should be same as manufacturing quantity"""
	if not self.work_order: return

	items_with_target_warehouse = []
	allowance_percentage = flt(frappe.db.get_single_value("Manufacturing Settings",
		"overproduction_percentage_for_work_order"))

	production_item, wo_qty = frappe.db.get_value("Work Order",
		self.work_order, ["production_item", "qty"])

	for d in self.get('items'):
		if (self.purpose != "Send to Subcontractor" and d.bom_no
			and flt(round(d.transfer_qty,3)) > flt(round(self.fg_completed_qty,3)) and d.item_code == production_item):
			frappe.throw(_("Quantity in row {0} ({1}) must be same as manufactured quantity {2}"). \
				format(d.idx, round(d.transfer_qty,3), round(self.fg_completed_qty,3)))

		if self.work_order and self.purpose == "Manufacture" and d.t_warehouse:
			items_with_target_warehouse.append(d.item_code)

	if self.work_order and self.purpose == "Manufacture":
		allowed_qty = wo_qty + (allowance_percentage/100 * wo_qty)
		#Finbyz Changes: self.fg_completed_qty to self.if self.fg_completed_quantity
		if self.fg_completed_quantity > allowed_qty:
			frappe.throw(_("For quantity {0} should not be grater than work order quantity {1}")
				.format(flt(self.fg_completed_quantity), wo_qty))

		if production_item not in items_with_target_warehouse:
			frappe.throw(_("Finished Item {0} must be entered for Manufacture type entry")
				.format(production_item))

def delete_auto_created_batches(self):
	pass


def on_update_after_submit(self,method):
	pass
	# update_yield(self)

def update_yield(self):
	cal_yield = 0
	cons = 0
	tot_quan = 0
	item_arr = list()
	item_map = dict()
	flag = 0
	if self.purpose == "Manufacture" and self.based_on:
		for d in self.items:
			if d.t_warehouse and not frappe.db.get_value("Item",d.item_code,"maintain_as_is_stock"):
				if d.t_warehouse:
					flag+=1		
				
				if d.item_code not in item_arr:
						item_map.setdefault(d.item_code, {'quantity':0, 'qty':0, 'yield_weights':0})
					
				item_map[d.item_code]['quantity'] += flt(d.quantity)
				item_map[d.item_code]['qty'] += flt(d.qty)
				item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.quantity)


			if flag == 1:
				# Last row object
				last_row = self.items[-1]

				# Last row batch_yield
				batch_yield = last_row.batch_yield

				# List of item_code from items table
				items_list = [row.item_code for row in self.items]

				# Check if items list has frm.doc.based_on value
				if self.based_on in items_list:
					# item_yield = 0.0
					# if item_map[self.based_on]['yield_weights'] > 0:
					# 	item_yield = item_map[self.based_on]['yield_weights'] / item_map[self.based_on]['quantity']

					# 	if item_yield:
					# 		cal_yield = flt(item_yield) * flt(last_row.qty / item_map[self.based_on]['quantity']) # Last row qty / sum of items of based_on item from map variable
					# 	else:
					cal_yield =  flt(last_row.qty / item_map[self.based_on]['quantity'])
				last_row.batch_yield = flt(cal_yield) * (flt(last_row.concentration) / 100.0)		
				batch_doc = frappe.get_doc("Batch",row.batch_no)
				batch_doc.db_set('batch_yield',last_row.batch_yield)
				batch_doc.db_set('concentration',last_row.concentration)

		# update finised item detail

		count = 0
		batch_yield = 0.0
		concentration = 0.0

		po = frappe.get_doc("Work Order", self.work_order)
		po.finish_item = []
		if po.bom_no:
			bom_doc = frappe.get_doc("BOM",po.bom_no)
		# po.append("finish_item",finished_item_list)							
		for row in self.items:
			if row.t_warehouse and not frappe.db.get_value("Item",row.item_code,"maintain_as_is_stock"):
				count += 1
				batch_yield += row.batch_yield
				concentration += row.concentration
				if bom_doc.multiple_finish_item:
					for bom_fi in bom_doc.multiple_finish_item:
						po.append("finish_item",{
							'item_code': row.item_code,
							'actual_qty': row.qty,
							'actual_valuation': row.valuation_rate,
							'lot_no': row.lot_no,
							'purity': row.concentration,
							'packing_size': row.packing_size,
							'no_of_packages': row.no_of_packages,
							'batch_yield': row.batch_yield,
							'batch_no': row.batch_no,
							"bom_cost_ratio":bom_fi.cost_ratio,
							"bom_qty_ratio":bom_fi.qty_ratio,
							"bom_qty":po.qty * bom_fi.qty_ratio / 100,
							"bom_yield":bom_fi.batch_yield
						})
				else:
					po.append("finish_item",{
						'item_code': row.item_code,
						'purity': row.concentration,	
						'batch_yield': row.batch_yield,
						'batch_no': row.batch_no,
						"bom_yield": bom_doc.batch_yield
					})
				
		
		for child in po.finish_item:
			child.db_update()
		po.db_set("batch_yield", flt(batch_yield))
		po.db_set("concentration", flt(concentration))
		
def set_batch_qc(self):
	for row in self.items:
		if row.quality_inspection:
			qi_doc = frappe.get_doc("Quality Inspection",row.quality_inspection)
			qi_doc.db_set("batch_no", row.batch_no, update_modified=False)	

	
def update_item_batches_based_on_fifo(self):
	if not self.get('get_batches_based_on_fifo'):
		return
	def get_item_details_custom(self,each_item):
		item = frappe.db.sql(
			"""select i.name, i.stock_uom, i.description, i.image, i.item_name, i.item_group,
				i.has_batch_no, i.sample_quantity, i.has_serial_no, i.allow_alternative_item,
				id.expense_account, id.buying_cost_center
			from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
			where i.name=%s
				and i.disabled=0
				and (i.end_of_life is null or i.end_of_life='0000-00-00' or i.end_of_life > %s)""",
			(self.company, each_item.get("item_code") or each_item.get("item_name"), nowdate()),
			as_dict=1,
		)
		if not item:
			frappe.throw(
				_("Item {0} is not active or end of life has been reached").format(each_item.get("item_code"))
			)

		return item[0]


	new_items=[]

	self.old_items={}
	for row in self.items:
		item = get_item_details_custom(self,row)
		if (
					row.get("s_warehouse", None)
					and row.get("qty")
					and item.get("has_batch_no")
				):
			if not self.old_items.get((row.item_code,row.s_warehouse)):
				self.old_items[(row.item_code,row.s_warehouse)]=[]

			self.old_items[(row.item_code,row.s_warehouse)].append(row)
		else:
			new_items.append(row)
	self.items=[]
	self.batches=[]
	for item_warehouse_group in self.old_items.values():
		self.batches=[]
		self.batches= get_fifo_batches(item_warehouse_group[0].item_code, item_warehouse_group[0].s_warehouse)
		for each_item in item_warehouse_group:
			item = get_item_details_custom(self,each_item)
			if (
					each_item.get("s_warehouse", None)
					and each_item.get("qty")
					and item.get("has_batch_no")
				):
				update_multiple_item_batch_based_on_fifo(self,each_item)

	self.get_batches_based_on_fifo=0
	if new_items:
		self.items.extend(new_items)

	set_concentration_based_on_batch(self)
	# frappe.throw(str(self.items))

def set_concentration_based_on_batch(self):
	for each in self.items:
		if not each.get('concentration') and each.batch_no:
			each.concentration = flt(frappe.db.get_value("Batch",each.batch_no,'concentration'))
		elif not each.get('concentration'):
			each.concentration = flt(100)

def get_fifo_batches(item_code, warehouse):
	batches = frappe.db.sql("""
		select 
			batch_id, sum(actual_qty) as qty,concentration from `tabBatch` join `tabStock Ledger Entry` ignore index (item_code, warehouse) 
			on (`tabBatch`.batch_id = `tabStock Ledger Entry`.batch_no )
		where 
			`tabStock Ledger Entry`.item_code = %s 
			and `tabStock Ledger Entry`.warehouse = %s 
			and (`tabBatch`.expiry_date >= CURDATE() or `tabBatch`.expiry_date IS NULL)
		group by `tabStock Ledger Entry`.batch_no
		having sum(actual_qty) > 0 
		order by `tabBatch`.creation """, (item_code, warehouse), as_dict=True)

	return batches

def update_multiple_item_batch_based_on_fifo(self,each_item):

	if not self.batches:
		return 
	
	
	remaining_qty=flt(each_item.qty,7)
	for idx,each_batch in enumerate(self.batches):
		if remaining_qty > 0 :
			if flt(each_batch.qty,7)< 0.000001:
				continue
			if idx == 0:
				use_qty=flt(each_batch.qty if remaining_qty > each_batch.qty else remaining_qty,7)
				if not use_qty:
					continue
				self.add_to_stock_entry_detail({
					each_item.item_code: {
							"from_warehouse": each_item.s_warehouse,
							"to_warehouse":each_item.t_warehouse,
							"qty": use_qty,
							"quantity": use_qty,
							"item_name": each_item.item_name,
							"item_code": each_item.item_code,
							"description": each_item.description,
							"stock_uom": each_item.stock_uom,
							"expense_account": each_item.expense_account,
							"cost_center": each_item.get('buying_cost_center'),
							"original_item": each_item.original_item,
							"batch_no": str(each_batch.batch_id),
							"item_group":each_item.get('item_group'),
							"is_process_loss":each_item.get('is_process_loss'),
							"is_scrap_item":each_item.get('is_scrap_item'),
							"is_finished_item":each_item.get('is_finished_item'),
							"concentration":flt(each_batch.concentration or each_item.get('concentration') or 100)
						}
					})
				remaining_qty -= use_qty
				update_used_batches(self,str(each_batch.batch_id),use_qty)
				# frappe.msgprint(str(f"{each_item.item_code} ----> existing		bid-{str(each_batch.batch_id)} qty-{use_qty} 				batches-{str(self.batches)}"))
			else:
				update_item=each_item.as_dict().copy()
				use_qty=flt(each_batch.qty if remaining_qty > each_batch.qty else remaining_qty,7)
				update_item.batch_no = each_batch.batch_id
				update_item.qty = use_qty
				update_item.quantity = use_qty
				remaining_qty -= use_qty
				if not use_qty:
					continue
				self.add_to_stock_entry_detail({
					each_item.item_code: {
							"from_warehouse": each_item.s_warehouse,
							"to_warehouse":each_item.t_warehouse,
							"qty": use_qty,
							"quantity": use_qty,
							"item_code": each_item.item_code,
							"item_name": each_item.item_name,
							"description": each_item.description,
							"stock_uom": each_item.stock_uom,
							"expense_account": each_item.expense_account,
							"cost_center": each_item.get('buying_cost_center'),
							"original_item": each_item.original_item,
							"batch_no": str(each_batch.batch_id),
							"item_group":each_item.get('item_group'),
							"is_process_loss":each_item.get('is_process_loss'),
							"is_scrap_item":each_item.get('is_scrap_item'),
							"is_finished_item":each_item.get('is_finished_item'),
							"concentration":flt(each_batch.concentration or each_item.get('concentration') or 100)
					}})
					
				update_used_batches(self, str(each_batch.batch_id),use_qty)
				# frappe.msgprint(str(f"{each_item.item_code} ----> new 	bid-{str(each_batch.batch_id)} qty-{use_qty} 			batches-{str(self.batches)}"))

		else:
			break


def update_used_batches(self,batch_id,qty):
	for idx,each in enumerate(self.batches):
		if each.batch_id == batch_id:
			each.qty-=qty
			break

def validate_finished_goods(self):
	"""
	1. Check if FG exists (mfg, repack)
	2. Check if Multiple FG Items are present (mfg)
	3. Check FG Item and Qty against WO if present (mfg)
	"""
	production_item, wo_qty, finished_items = None, 0, []

	wo_details = frappe.db.get_value("Work Order", self.work_order, ["production_item", "qty"])
	if wo_details:
		production_item, wo_qty = wo_details
		bom_multi_doc = frappe.get_doc("BOM", frappe.db.get_value("Work Order" , self.work_order , "bom_no"))
		production_item = [d.item_code for d in bom_multi_doc.multiple_finish_item]
		if not production_item:
			production_item.append(frappe.db.get_value("Work Order",self.work_order , "production_item"))
	for d in self.get("items"):
		if d.is_finished_item:
			if not self.work_order:
				# Independent MFG Entry/ Repack Entry, no WO to match against
				finished_items.append(d.item_code)
				continue

			if d.item_code not in production_item:
				frappe.throw(
					_("Finished Item {0} does not match with Work Order {1}").format(
						d.item_code, self.work_order
					)
				)
			elif flt(d.transfer_qty) > flt(self.fg_completed_qty):
				frappe.throw(
					_("Quantity in row {0} ({1}) must be same as manufactured quantity {2}").format(
						d.idx, d.transfer_qty, self.fg_completed_qty
					)
				)

			finished_items.append(d.item_code)

	if not finished_items:
		frappe.throw(
			msg=_("There must be atleast 1 Finished Good in this Stock Entry").format(self.name),
			title=_("Missing Finished Good"),
			exc=FinishedGoodError,
		)

	if self.purpose == "Manufacture":
		allowance_percentage = flt(
			frappe.db.get_single_value(
				"Manufacturing Settings", "overproduction_percentage_for_work_order"
			)
		)
		allowed_qty = wo_qty + ((allowance_percentage / 100) * wo_qty)

		# No work order could mean independent Manufacture entry, if so skip validation
		if self.work_order and flt(self.fg_completed_qty) > allowed_qty:
			frappe.throw(
				_("For quantity {0} should not be greater than allowed quantity {1}").format(
					flt(self.fg_completed_qty), allowed_qty
				)
			)

