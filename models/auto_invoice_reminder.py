from odoo import api, fields, models
from datetime import date, timedelta
import base64
import logging

_logger = logging.getLogger(__name__)

class AutoInvoiceReminder(models.Model):
    _inherit = 'account.move'

    @api.model
    def _cron_send_pending_invoice_report(self):
        """
        Generate report for pending invoices older than X days,
        group by customer, and send customer-specific reports via email.
        """
        _logger.info("Starting _cron_send_pending_invoice_report...")
        today = date.today()
        
        # Hardcoding 7 days to remove the ir.config_parameter as a variable.
        days_old = 7
        
        due_date_threshold = today - timedelta(days=days_old)
        _logger.info(f"Running for invoices due before {due_date_threshold} (days_old: {days_old})")

        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '<', due_date_threshold)
        ]

        all_pending_invoices = self.env['account.move'].search(domain)

        if not all_pending_invoices:
            _logger.info("No pending invoices found matching criteria. Exiting cron.")
            return True

        # Get the mail template and report action
        try:
            # Using new v4 ID
            mail_template = self.env.ref('auto_invoice_reminder_daysfilter.email_template_pending_invoices_v4')
            
            # Using new v4 ID
            report_action_xml_id = 'auto_invoice_reminder_daysfilter.action_pending_invoice_report_daysfilter_v4'
            report_action = self.env.ref(report_action_xml_id)
            
        except ValueError as e:
            _logger.error(f"Could not find template or report action: {e}. Ensure module is installed correctly.")
            return False

        # Group invoices by customer (partner_id)
        invoices_by_customer = {}
        for invoice in all_pending_invoices:
            partner = invoice.partner_id
            if partner not in invoices_by_customer:
                invoices_by_customer[partner] = []
            invoices_by_customer[partner].append(invoice.id)

        _logger.info(f"Found pending invoices for {len(invoices_by_customer)} customers.")
        
        email_from = self.env.user.email_formatted or self.env.company.email or mail_template.email_from

        for customer, invoice_ids in invoices_by_customer.items():
            if not customer.email:
                _logger.warning(f"Customer '{customer.name}' (ID: {customer.id}) has no email. Skipping.")
                continue

            try:
                # Generate PDF report for *this* customer's invoices
                pdf_report, _ = report_action._render_qweb_pdf(invoice_ids)
                
                attachment = self.env['ir.attachment'].create({
                    'name': f'Pending_Invoices_{customer.name.replace(" ", "_")}_{today}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_report),
                    'res_model': 'account.move',
                    'mimetype': 'application/pdf',
                })

                subject = mail_template.subject
                body_html = mail_template.body_html

                mail_values = {
                    'subject': subject,
                    'body_html': body_html,
                    'email_to': customer.email,
                    'email_from': email_from,
                    'attachment_ids': [attachment.id],
                }
                
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.send()
                
                _logger.info(f"Sent pending invoice report to '{customer.name}' ({customer.email}).")

            except Exception as e:
                _logger.error(f"Failed to send invoice report to '{customer.name}' (ID: {customer.id}): {e}")
        
        _logger.info("Finished _cron_send_pending_invoice_report.")
        return True