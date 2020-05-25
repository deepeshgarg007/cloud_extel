from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, add_months
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.general_ledger import make_gl_entries

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