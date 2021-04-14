// Copyright (c) 2020 Software to Hardware Ltd. and contributors
// For license information, please see license.txt

var fraud_prevention_headers = function() {
    return {
        "TimezoneOffsetMinutes": `${new Date().getTimezoneOffset()}`,
        "ScreenWidth": `${screen.width}`,
        "ScreenHeight": `${screen.height}`,
        "ScreenScalingFactor": `${window.devicePixelRatio}`,
        "ScreenColorDepth": `${screen.colorDepth}`,
        "WindowWidth": `${window.innerWidth}`,
        "WindowHeight": `${window.innerHeight}`,
        "UA": `${navigator.userAgent}`,
        "Plugins": Array.from(navigator.plugins, plugin => plugin && plugin.name)
                    .filter((name) => name).join(",")
    }
}

frappe.ui.form.on('UK VAT Return', {
	refresh: function(frm) {

		if(!frm.is_new()) {

			if (!frm.doc.docstatus==1) {
				frm.add_custom_button(__('Save and recalculate'), function() {
					frm.save()
				});
			}

			frm.add_custom_button(__('Show drilldown'), function() {
				frappe.set_route("query-report", "UK VAT Return Drilldown",
					{"company": frm.doc.company,
					 "period_start_date": frm.doc.period_start_date,
					 "period_end_date": frm.doc.period_end_date});
			});


		}

	},

	fetch_returns_hmrc: function(frm) {

		frappe.call({
			"method" : "uk_vat.uk_vat_return.doctype.uk_vat_return.uk_vat_return.get_open_obligations",
			"args" : {
				company_name : frm.doc.company,
                fraud_prevention: fraud_prevention_headers()
			},
			"callback" : function(r) {

				let obligations = r.message;

				if (obligations.length < 1) {
					frappe.msgprint("There are no open obligations.");
					return;
				}

				var options = [];
				var option_map = {};
				obligations.forEach(o => {
					var option = o["start"] + " to " + o["end"] + ", Due: " + o["due"] + ")";
					option_map[option] = o;
					options.push(option);
				});

				let d = new frappe.ui.Dialog({
					title: 'Select open obligation',
					fields: [
						{
							label: 'Obligations',
							fieldname: 'obligation',
							fieldtype: 'Select',
							options: options
						}
					],
					primary_action_label: 'Select',
					primary_action(values) {
						let o = option_map[values.obligation];
						console.log(o);
						cur_frm.set_value("period_start_date", o["start"]);
						cur_frm.set_value("period_end_date", o["end"]);
						cur_frm.dirty();
						cur_frm.save();
						d.hide();
					}
				});

				d.show();

			}
		});

	},

	submit_to_hmrc: function(frm) {

		frappe.confirm(
			'Are you sure you would like to submit this VAT information?',
			function(){

				frappe.call({
					"method" : "uk_vat.uk_vat_return.doctype.uk_vat_return.uk_vat_return.submit_vat_return",
					"args" : {
						name : frm.doc.name,
						is_finalised: frm.doc.is_finalised,
                        fraud_prevention: fraud_prevention_headers()
					},
					"callback" : function(r) {
						frappe.msgprint("VAT return submitted to HMRC!");
						frm.reload_doc();
					}
				});


			},
			function(){
				show_alert('VAT return was NOT submitted.')
			}
		);

	}

});
