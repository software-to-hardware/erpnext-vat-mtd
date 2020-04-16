// Copyright (c) 2020 Software to Hardware Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('HMRC API Settings', {
	refresh: function(frm) {

		frm.add_custom_button(__('Test HMRC Connectivity'), function() {
			frappe.call({
				"method" : "uk_vat.uk_vat_return.doctype.hmrc_api_settings.hmrc_api_settings.test_api",
				"args" : {
					name : frm.doc.name,
				},
				"callback" : function(r){
					frappe.msgprint("HMRC connectivity test success!");
				}
			});
		});

	}
});
