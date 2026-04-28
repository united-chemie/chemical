# import erpnext
# from chemical.batch_valuation_overrides import get_incoming_rate as my_incoming_rate, process_sle as my_process_sle, get_args_for_incoming_rate as my_get_args_for_incoming_rate, update_raw_materials_supplied_based_on_bom as my_update_raw_materials_supplied_based_on_bom, update_stock_ledger as my_update_stock_ledger
# from erpnext.stock.stock_ledger import update_entries_after
# from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
# from erpnext.controllers.buying_controller import BuyingController
# from erpnext.controllers.selling_controller import SellingController

# #update_entries_after.process_sle = my_process_sle
# StockEntry.get_args_for_incoming_rate = my_get_args_for_incoming_rate
# BuyingController.update_raw_materials_supplied_based_on_bom = my_update_raw_materials_supplied_based_on_bom
# SellingController.update_stock_ledger = my_update_stock_ledger