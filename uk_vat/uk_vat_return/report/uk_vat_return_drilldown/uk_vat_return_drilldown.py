# -*- coding: utf-8 -*-
# Copyright (c) 2020 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from uk_vat.uk_vat_return.doctype.uk_vat_return.uk_vat_return import get_vat_return, vat_return_schema

def execute(filters=None):

	if filters.company is None or \
		filters.period_start_date is None or \
		filters.period_end_date is None:

		return [], []

	columns = [	{'fieldname': 'box', 
				'label': 'VAT Return Field', 
				'fieldtype': 'Data', 
				'options': '', 
				'width': 300},
				{'fieldname': 'line_item', 
				 'label': 'Line Item',
				 'fieldtype': 'Data', 
				 'options': '', 
				 'width': 150
				 },
				{'fieldname': 'item_tax_template', 
				 'label': 'Item Tax Template',
				 'fieldtype': 'Link', 
				 'options': 'Item Tax Template', 
				 'width': 120
				 },
				{'fieldname': 'contribution',
				 'label': 'Contribution',
				 'fieldtype': 'Currency',
				 'options': '',
				 'width': 120}
	]

	drilldown = {}
	vat_return = get_vat_return(filters.company, 
								filters.period_start_date,
								filters.period_end_date,
								drilldown)

	box_order = [
		"vatDueSales",
		"vatDueAcquisitions",
		"totalVatDue",
		"vatReclaimedCurrPeriod",
		"netVatDue",
		"totalValueSalesExVAT",
		"totalValuePurchasesExVAT",
		"totalValueGoodsSuppliedExVAT",
		"totalAcquisitionsExVAT"	
	]

	data = []
	for box in box_order:
		box_name = "Box %d: %s" % (vat_return_schema[box][0], 
								   vat_return_schema[box][2])
		data += [
			{'box': box_name,
			 'contribution': vat_return[box],
                         'is_group': 1}
		]
		for drilldown_item in drilldown[box]:
			data += [
				{'box': drilldown_item[0].name,
				 'parent_box': box_name,
				 'line_item': drilldown_item[0].item_name,
				 'item_tax_template': drilldown_item[0].item_tax_template,
				 'contribution': drilldown_item[1],
				 'indent': 1}
			]

	return columns, data




 
