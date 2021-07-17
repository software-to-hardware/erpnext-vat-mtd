# -*- coding: utf-8 -*-
# Copyright (c) 2020 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import get_url, nowdate, date_diff, flt
import json
import uk_vat.uk_vat_return.hmrc_api.vat as vat_api
import datetime

vat_return_schema = {
									# Box Number, Source of value, Description, Precision
	"vatDueSales":					[1, "vat", "VAT due on sales", 2],
	"vatDueAcquisitions":			[2, "vat", "VAT due on EU acquisitions", 2],
	"totalVatDue":					[3, None, "Total VAT due", 2],
	"vatReclaimedCurrPeriod":		[4, "vat", "VAT reclaimed on purchase", 2],
	"netVatDue": 					[5, None, "Net VAT", 2],
	"totalValueSalesExVAT": 		[6, "base_amount", "Total sales, ex. VAT", 0],
	"totalValuePurchasesExVAT": 	[7, "base_amount", "Total purchases, ex. VAT", 0],
	"totalValueGoodsSuppliedExVAT": [8, "base_amount", "Total EC supply of goods, ex VAT", 0],
	"totalAcquisitionsExVAT": 		[9, "base_amount", "Total EC acquisitions of goods, ex. VAT", 0]
}

class UKVATReturn(Document):

	def before_save(self):

		vat_return = get_vat_return(self.company,
									self.period_start_date,
									self.period_end_date)

		# Box 1
		self.vat_output = vat_return["vatDueSales"]

		# Box 2
		self.vat_eu_acquisitions = vat_return["vatDueAcquisitions"]

		# Box 3
		self.vat_due_total = vat_return["totalVatDue"]

		# Box 4
		self.vat_input = vat_return["vatReclaimedCurrPeriod"]

		# Box 5
		self.vat_net = vat_return["netVatDue"]

		# Box 6
		self.total_output_exvat = vat_return["totalValueSalesExVAT"]

		# Box 7
		self.total_input_exvat = vat_return["totalValuePurchasesExVAT"]

		# Box 8
		self.total_ec_goods_output = vat_return["totalValueGoodsSuppliedExVAT"]

		# Box 9
		self.total_ec_goods_input = vat_return["totalAcquisitionsExVAT"]


def get_transactions(company, invoice_type, period_start_date, period_end_date):

	transactions = frappe.db.sql("""
		select invoice.name as name, ii.item_name, ii.item_code, ii.idx,
			ii.base_amount, ii.item_tax_template,
		tt.vat_rate, tt.vat_is_reverse_charge, tt.vat_transaction_type,
		tt.vat_rules from 
			`tab{invoice_type} Invoice` invoice
		inner join `tab{invoice_type} Invoice Item` ii on
			ii.parent = invoice.name
		left join `tabItem Tax Template` tt on
			tt.name = ii.item_tax_template
		where
			invoice.docstatus = 1 and
			invoice.posting_date >= %s and
			invoice.posting_date <= %s and
			tt.vat_is_in_vat_return = 1
		""".format(invoice_type=invoice_type), 
			(period_start_date, period_end_date), as_dict=True)

	# Calculate the VAT for each line
	for t in transactions:
		if t["item_tax_template"] is None:
			frappe.throw(
				"Item Tax Template not set on one of the lines in invoice %s" %
				t["name"])
		if t["vat_rate"] is None:
			frappe.throw("VAT rate not set on Item Tax Template %s" %
				t["item_tax_template"])

		t["vat"] = t["base_amount"] * (t["vat_rate"] / 100.0)

	return transactions


def get_vat_return(company, period_start_date, period_end_date, drilldown=None):

	if period_start_date > period_end_date:
		frappe.throw("Cannot create VAT return where start date is after the end date.")

	# VAT return as required by UK Government API (HMRC).
	vat_return = {k: 0.0 for k in vat_return_schema}
	vat_return["finalised"] = False

	# If requested, initialise drilldown
	if drilldown is not None:
		for k in vat_return_schema:
			drilldown[k] = []

	# We centralise all changes to the VAT return so we can record the source
	# of each change.
	def increment(item, field_list):
		for field in field_list:
			amount = item[vat_return_schema[field][1]]
			vat_return[field] += amount
			if drilldown is not None:
				drilldown[field] += [[item, amount]]

	#
	# SALES (Output VAT)
	#
	for sale in get_transactions(company, "Sales", 
								 period_start_date, period_end_date):
		
		# EU rules
		if sale["vat_rules"]=="EU":

			if sale["vat_transaction_type"]=="Goods":
				# Boxes 6 and 8
				increment(sale, 
					("totalValueSalesExVAT", "totalValueGoodsSuppliedExVAT"))
			elif sale["vat_transaction_type"]=="Services":
				# Box 6
				increment(sale, ("totalValueSalesExVAT",))
			else:
				frappe.throw(
					"Unsupported vat_transaction_type '%s' for EU rules" % 
					repr(sale["vat_transaction_type"]))

		# UK trade
		elif sale["vat_rules"]=="UK":

			# Boxes 1 and 6
			increment(sale, ("vatDueSales","totalValueSalesExVAT"))
		
		# RoW
		elif sale["vat_rules"]=="Rest of World":

			if sale["vat_transaction_type"]=="Goods" or \
			   sale["vat_transaction_type"]=="Services":
				# Box 6
				increment(sale, ("totalValueSalesExVAT",))
			else:
				frappe.throw(
					"Unsupported vat_transaction_type '%s' for RoW rules" % 
					repr(sale["vat_transaction_type"]))

		else:
			frappe.throw("Unknown vat_rules: %s" % repr(sale["vat_rules"]))

	#
	# Purchases (Input VAT)
	#
	for purchase in get_transactions(company, "Purchase", 
									 period_start_date, period_end_date):
		
		# EU rules
		if purchase["vat_rules"]=="EU":

			if purchase["vat_transaction_type"]=="Goods":

				# Boxes 2, 4, 7 and 9
				increment(purchase, 
					("vatDueAcquisitions", "vatReclaimedCurrPeriod",
					 "totalValuePurchasesExVAT","totalAcquisitionsExVAT"))

			elif purchase["vat_transaction_type"]=="Services":

				# Boxes 1, 4, 6 and 7
				increment(purchase,
					("vatDueSales", "vatReclaimedCurrPeriod", 
					 "totalValueSalesExVAT", "totalValuePurchasesExVAT"))

			else:
				frappe.throw(
					"Unsupported vat_transaction_type '%s' for EU rules" % 
					repr(purchase["vat_transaction_type"]))

		# UK trade
		elif purchase["vat_rules"]=="UK":

			if purchase["vat_is_reverse_charge"]:

				# Boxes 1, 4, 6 and 7
				increment(purchase,
					("vatDueSales", "vatReclaimedCurrPeriod", 
					 "totalValueSalesExVAT", "totalValuePurchasesExVAT"))

			else:

				# Boxes 4 and 7
				increment(purchase,
					("vatReclaimedCurrPeriod", "totalValuePurchasesExVAT"))
	
		# RoW
		elif purchase["vat_rules"]=="Rest of World":

			if purchase["vat_transaction_type"]=="Goods":

				# Boxes 4 and 7
				increment(purchase,
					("vatReclaimedCurrPeriod", "totalValuePurchasesExVAT"))

			elif purchase["vat_transaction_type"]=="Services":

				# Boxes 1, 4, 6 and 7
				increment(purchase,
					("vatDueSales", "vatReclaimedCurrPeriod", 
					 "totalValueSalesExVAT", "totalValuePurchasesExVAT"))

		
		else:
			frappe.throw("Unknown vat_rules: %s" % repr(purchase["vat_rules"]))

	# Box 3 = Box 1 + Box 2
	vat_return["totalVatDue"] += vat_return["vatDueSales"] + \
		vat_return["vatDueAcquisitions"]

	# Box 5 = |Box 3 - Box 4|
	vat_return["netVatDue"] = abs(vat_return["totalVatDue"] -
		vat_return["vatReclaimedCurrPeriod"])

	# All figures need to be of required precision
	for f in vat_return_schema.keys():
		vat_return[f] = flt(vat_return[f], vat_return_schema[f][3])

	return vat_return

@frappe.whitelist()
def get_open_obligations(company_name):	
	return vat_api.get_open_obligations(company_name)

@frappe.whitelist()
def submit_vat_return(name, is_finalised):

	doc = frappe.get_doc("UK VAT Return", name)

	# Match dates on the form to an open obgligation
	obligations = vat_api.get_open_obligations(doc.company)
	selected_obligation = None
	print(type(doc.period_end_date))
	for o in obligations:
		start = datetime.datetime.strptime(o["start"], "%Y-%m-%d").date()
		end = datetime.datetime.strptime(o["end"], "%Y-%m-%d").date()
		if doc.period_start_date==start and doc.period_end_date==end:
			selected_obligation = o
			break
	else:
		frappe.throw("The selected dates do not match any open HMRC obligations")

	# Generate submission document
	vat_return = {
		"vatDueSales": doc.vat_output,
		"vatDueAcquisitions": doc.vat_eu_acquisitions,
		"totalVatDue": doc.vat_due_total,
		"vatReclaimedCurrPeriod": doc.vat_input,
		"netVatDue": doc.vat_net,
		"totalValueSalesExVAT": int(doc.total_output_exvat),
		"totalValuePurchasesExVAT": int(doc.total_input_exvat),
		"totalValueGoodsSuppliedExVAT": int(doc.total_ec_goods_output),
		"totalAcquisitionsExVAT": int(doc.total_ec_goods_input),
		"finalised": True if is_finalised else False,
		"periodKey": selected_obligation["periodKey"]
	}

	# Submit return to HMRC
	response, headers = vat_api.submit_return(doc.company, vat_return)
	if response.get("errors"):
		frappe.throw("\n".join({e["message"] for e in response["errors"]}),
		title=response["message"])

	# Save response
	doc.hmrc_correlation_id = headers["X-CorrelationId"]
	doc.hmrc_receipt_id = headers["Receipt-ID"]
	doc.hmrc_receipt_timestamp = headers["Receipt-Timestamp"]
	doc.hmrc_period_key = selected_obligation["periodKey"]
	doc.hmrc_processing_date = response.get("processingDate")
	doc.hmrc_form_bundle_number = response.get("formBundleNumber")
	doc.hmrc_payment_indicator = response.get("paymentIndicator")
	doc.hmrc_charge_reference_number = response.get("chargeRefNumber")
	doc.hmrc_vrn = vat_api.get_vrn(doc.company)
	doc.is_finalised = is_finalised
	doc.docstatus = 1
	doc.save()
