from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, add_months, add_days, flt
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions

def post_tds_gl_entries(payment_entry, method):
	for d in payment_entry.get("deductions"):
		gl_entries = []
		if payment_entry.party_type == 'Customer':
			account_fiscal_year_map = frappe._dict(frappe.get_all('TDS Accounts', fields=['fiscal_year', 'tds_account'],
				filters={'parent': payment_entry.company}, as_list=1))

			gross_tds_account = frappe.db.get_value('Company', payment_entry.company, 'gross_tds_account')
			booked_invoices = []

			for invoice in payment_entry.get('references'):
				if invoice.reference_name not in booked_invoices:
					doc = frappe.get_doc('Sales Invoice', invoice.reference_name)
					for item in doc.get('items'):
						service_start_date = getdate(item.service_start_date)
						service_end_date = getdate(item.service_end_date)

						if item.enable_deferred_revenue:
							no_of_months = (service_end_date.year - service_start_date.year) * 12 + \
								(service_end_date.month - service_start_date.month)

							for i in range(no_of_months):
								fiscal_year = get_fiscal_year(date=add_months(service_start_date, i))[0]

								tds_account = account_fiscal_year_map.get(fiscal_year)

								tds_amount_to_consider = d.amount * (item.amount /doc.net_total)

								amount = tds_amount_to_consider / no_of_months

								gl_entries.append(
									payment_entry.get_gl_dict({
										"account": tds_account,
										"against": payment_entry.party,
										"debit": amount,
										"debit_in_account_currency": amount,
										"cost_center": item.cost_center
									}, payment_entry.party_account_currency, item=item)
								)

								gl_entries.append(
									payment_entry.get_gl_dict({
										"account": d.account,
										"against": payment_entry.party,
										"credit": amount,
										"credit_in_account_currency": amount,
										"cost_center": item.cost_center
									}, payment_entry.party_account_currency, item=item)
								)
						else:
							amount = d.amount * (item.amount/doc.net_total)
							fiscal_year = get_fiscal_year(date=payment_entry.posting_date)[0]
							tds_account = account_fiscal_year_map.get(fiscal_year)

							gl_entries.append(
								payment_entry.get_gl_dict({
									"account": tds_account,
									"against": payment_entry.party,
									"debit": amount,
									"debit_in_account_currency": amount,
									"cost_center": item.cost_center
								}, payment_entry.party_account_currency, item=item)
							)

							gl_entries.append(
								payment_entry.get_gl_dict({
									"account": d.account,
									"against": payment_entry.party,
									"credit": amount,
									"credit_in_account_currency": amount,
									"cost_center": item.cost_center
								}, payment_entry.party_account_currency, item=item)
							)

					booked_invoices.append(invoice.reference_name)

					make_gl_entries(gl_entries)


# def post_grn_entries(posting_date=None):
# 	if not posting_date:
# 		posting_date = add_days(getdate(), -1)

# 	accounting_dimensions = get_accounting_dimensions()

# 	dimension_fields = ['i.cost_center']

# 	for dimension in accounting_dimensions:
# 		dimension_fields.append('i.{0}'.format(dimension))

# 	purchase_receipt_items = frappe.db.sql("""
# 		SELECT i.name, i.item_code, i.parent, i.base_net_amount, i.months,
# 			i.expense_account, i.cost_center, i.project, {dimension_fields}
# 		FROM `tabPurchase Receipt Item` i, `tabPurchase Receipt` p
# 		WHERE i.parent = p.name
# 			and i.is_fixed_asset = 0
# 			and p.posting_date <= %s
# 			and p.docstatus = 1
# 			and p.status = 'To Bill'
# 	""".format(dimension_fields = ', '.join(dimension_fields)), (posting_date), as_dict=1)

# 	voucher_detail_no_list = [d.name for d in purchase_receipt_items]

# 	booked_grn_amounts_map = frappe._dict(frappe.db.sql("""
# 		SELECT voucher_detail_no, sum(credit_in_account_currency) as amount
# 		FROM `tabGL Entry`
# 		WHERE voucher_type = 'Purchase Receipt' and
# 		voucher_detail_no in (%s)
# 		GROUP BY voucher_detail_no
# 	""" % (','.join(['%s'] * len(voucher_detail_no_list))), tuple(voucher_detail_no_list), as_list=1))

# 	for pr in purchase_receipt_items:
# 		if pr.base_net_amount > flt(booked_grn_amounts_map.get(pr.name)):
# 			doc = frappe.get_cached_doc('Purchase Receipt', pr.parent)

# 			expense_account = frappe.get_cached_value('Company', doc.company, 'default_expense_account')
# 			provision_account = frappe.get_cached_value('Company', doc.company, 'provision_account')

# 			stock_items = doc.get_stock_items()
# 			if pr.item_code not in stock_items:
# 				gl_entries = []
# 				months = pr.months or 12
# 				amount = pr.base_net_amount / months

# 				gl_entries.append(doc.get_gl_dict({
# 					'account': pr.expense_account or expense_account,
# 					'debit': amount,
# 					'debit_in_account_currency': amount,
# 					'voucher_detail_no': pr.name,
# 					'posting_date': posting_date,
# 					'cost_center': pr.cost_center,
# 					'project': pr.project
# 				}, item=pr))

# 				gl_entries.append(doc.get_gl_dict({
# 					'account': provision_account,
# 					'credit': amount,
# 					'credit_in_account_currency': amount,
# 					'voucher_detail_no': pr.name,
# 					'posting_date': posting_date,
# 					'cost_center': pr.cost_center,
# 					'project': pr.project
# 				}, item=pr))

# 				make_gl_entries(gl_entries)

# def validate_purchase_invoice(doc, method):
# 	for item in doc.get('items'):
# 		expense_account = item.expense_account
# 		voucher_detail = item.pr_detail

# 		provision_account = frappe.get_cached_value('Company', doc.company, 'provision_account')

# 		booked_expense = frappe.db.sql(
# 			"""
# 				SELECT sum(debit_in_account_currency - credit_in_account_currency)
# 				FROM `tabGL Entry` where voucher_detail_no = %s and account = %s
# 			""", (voucher_detail, expense_account)
# 		)[0][0]

# 		allow_without_pr = frappe.db.get_value('Supplier', doc.supplier, 'allow_purchase_invoice_creation_without_purchase_receipt')

# 		if doc.net_total > flt(booked_expense) and not allow_without_pr:
# 			frappe.throw(_("Row {0}: Purchase Receipt for Item {1} is created only for amount {2}").format(
# 				item.idx, frappe.bold(item.item_code), frappe.bold(booked_expense)))
# 		else:
# 			gl_entries = []
# 			gl_entries.append(doc.get_gl_dict({
# 				'account': provision_account,
# 				'debit': doc.base_net_total,
# 				'debit_in_account_currency': doc.base_net_total,
# 				'voucher_detail_no': voucher_detail,
# 				'posting_date': doc.posting_date,
# 				'cost_center': item.cost_center,
# 				'project': item.project
# 			}, item=item))

# 			gl_entries.append(doc.get_gl_dict({
# 				'account': expense_account,
# 				'credit': doc.base_net_total,
# 				'credit_in_account_currency': doc.base_net_total,
# 				'voucher_detail_no': voucher_detail,
# 				'posting_date': doc.posting_date,
# 				'cost_center': item.cost_center,
# 				'project': item.project
# 			}, item=item))

# 			make_gl_entries(gl_entries)