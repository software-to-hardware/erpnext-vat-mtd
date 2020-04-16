// Copyright (c) 2020 Software to Hardware Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('HMRC Authorisations', {

	request_authorisations: function(frm) {

		frappe.call({
			method: "uk_vat.uk_vat_return.doctype.hmrc_authorisations.hmrc_authorisations.authorize_access",
			args: {
				name : frm.doc.name,
			},
			callback: function(r) {
				if (!r.exc) {
					frm.save();
					window.open(r.message.url);
				}
			}
		});
	}
});
