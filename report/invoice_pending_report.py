from odoo import models, fields, api

class PendingInvoiceReport(models.AbstractModel):
    _name = 'report.auto_invoice_reminder_daysfilter.invoice_pending_tpl'
    _description = 'Pending Invoice Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Generate report values for pending invoice report
        """
        docs = self.env['account.move'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'date': fields.Date.today(),
        }