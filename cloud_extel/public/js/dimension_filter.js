
let doctypes_with_dimensions = ["GL Entry", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Asset",
"Expense Claim", "Stock Entry", "Budget", "Payroll Entry", "Delivery Note", "Shipping Rule", "Loyalty Program",
"Fee Schedule", "Fee Structure", "Stock Reconciliation", "Travel Request", "Fees", "POS Profile", "Opening Invoice Creation Tool",
"Subscription", "Purchase Order", "Journal Entry", "Material Request", "Purchase Receipt", "Landed Cost Item", "Asset"];


doctypes_with_dimensions.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		cost_center: function(frm) {
			frappe.call({
				'method': 'frappe.client.get_list',
				'args': {
					'filters':{'business_segment': frm.doc.cost_center},
					'doctype': 'Business Segment',
					'fields': ['parent'],
					'parent': 'Telecom Region'
				},
				'callback': function(r) {
					frm.set_query('telecom_region', function() {
						let region_list = r.message;
						region_list = region_list.map(pt => pt.parent);

						return {
							filters: {
								'name': ['in', region_list]
							}
						}
					});
				}
			});
		},
	});
});