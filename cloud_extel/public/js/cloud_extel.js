!function(){"use strict";["GL Entry","Sales Invoice","Purchase Invoice","Payment Entry","Asset","Expense Claim","Stock Entry","Budget","Payroll Entry","Delivery Note","Shipping Rule","Loyalty Program","Fee Schedule","Fee Structure","Stock Reconciliation","Travel Request","Fees","POS Profile","Opening Invoice Creation Tool","Subscription","Purchase Order","Journal Entry","Material Request","Purchase Receipt","Landed Cost Item","Asset"].forEach(function(e){frappe.ui.form.on(e,{refresh:function(e){e.set_query("city",function(){return{filters:{gst_state:e.doc.territory}}})},cost_center:function(e){frappe.call({method:"frappe.client.get_list",args:{filters:{business_segment:e.doc.cost_center},doctype:"Business Segment",fields:["parent"],parent:"Telecom Region"},callback:function(t){e.set_query("telecom_region",function(){var e=t.message;return{filters:{name:["in",e=e.map(function(e){return e.parent})]}}})}})}})})}();
//# sourceMappingURL=cloud_extel.js.map
