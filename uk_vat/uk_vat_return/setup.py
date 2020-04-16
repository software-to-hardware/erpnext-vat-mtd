# -*- coding: utf-8 -*-
# Copyright (c) 2020 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup(company=None, patch=True):
    make_custom_fields()

def make_custom_fields(update=True):

    vat_item_fields = [

        dict(fieldname='vat_section', label='VAT Details', fieldtype='Section Break',
	        print_hide=1, insert_after='taxes'),

        dict(fieldname='vat_is_in_vat_return', label='Include in VAT return',
            fieldtype='Check', insert_after='vat_section'),

        dict(fieldname='vat_rules', label='VAT Rules', fieldtype='Select', 
            options='UK\nEU\nRest of World', insert_after='vat_is_in_vat_return'),

        dict(fieldname='vat_is_reverse_charge', label='Reverse charge applies',
            fieldtype='Check', insert_after='vat_is_eu'),

        dict(fieldname='vat_transaction_type', label='Transaction type', fieldtype='Select',
            options='Goods\nServices\nNot applicable', insert_after='vat_is_reverse_charge'),

        dict(fieldname='vat_rate', label='VAT rate', fieldtype='Float',
            insert_after='vat_transaction_type'),
    ]

    custom_fields = {
        'Item Tax Template': vat_item_fields,
    }

    create_custom_fields(custom_fields, update=update)

