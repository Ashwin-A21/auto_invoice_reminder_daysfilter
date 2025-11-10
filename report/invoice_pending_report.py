from odoo import models, fields

class PendingInvoiceReport(models.AbstractModel):
    # Shortened name to avoid DB table name length limit
    _name = 'report.auto_invoice_reminder_daysfilter.invoice_pending_tpl'
    _description = 'Pending Invoice Report'

    def _get_report_values(self, docids, data=None):
        if docids:
            docs = self.env['account.move'].browse(docids)
        else:
            # Fallback for manual report generation
            today = fields.Date.today()
            docs = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', today)
            ])
            
        return {
            'docs': docs,
            'date': fields.Date.today(),
        }