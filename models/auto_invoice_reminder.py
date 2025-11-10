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
            ('invoice_date_due', '<=', due_date_threshold)
        ]

        all_pending_invoices = self.env['account.move'].search(domain)
        _logger.info(f"Found {len(all_pending_invoices)} total pending invoices matching criteria.")

        if not all_pending_invoices:
            _logger.info("No pending invoices found matching criteria. Exiting cron.")
            return True

        # Get the mail template and report action
        try:
            mail_template = self.env.ref('auto_invoice_reminder_daysfilter.email_template_pending_invoices_v4')
            _logger.info(f"Mail template found: {mail_template.name}")
            
            # Use the correct XML ID without version suffix
            report_action = self.env.ref('auto_invoice_reminder_daysfilter.action_pending_invoice_report')
            _logger.info(f"Report action found: {report_action.name}")
            
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

        _logger.info(f"Grouped invoices for {len(invoices_by_customer)} unique customers.")
        
        # Get email_from
        email_from = self.env.company.email or self.env.user.email or 'noreply@example.com'
        _logger.info(f"Sending emails from: {email_from}")

        sent_count = 0
        failed_count = 0

        for customer, invoice_ids in invoices_by_customer.items():
            if not customer.email:
                _logger.warning(f"Customer '{customer.name}' (ID: {customer.id}) has no email. Skipping.")
                failed_count += 1
                continue

            try:
                _logger.info(f"Processing {len(invoice_ids)} invoices for customer: {customer.name} ({customer.email})")
                _logger.info(f"Invoice IDs to process: {invoice_ids}")
                
                # Generate PDF report for *this* customer's invoices
                _logger.info(f"Attempting to render PDF report...")
                # In Odoo 17, use the env to render the report
                pdf_content, report_format = self.env['ir.actions.report']._render_qweb_pdf(
                    'auto_invoice_reminder_daysfilter.action_pending_invoice_report',
                    res_ids=invoice_ids
                )
                _logger.info(f"PDF generated successfully for {customer.name}, size: {len(pdf_content)} bytes")
                
                # Create attachment
                attachment = self.env['ir.attachment'].create({
                    'name': f'Pending_Invoices_{customer.name.replace(" ", "_")}_{today}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'account.move',
                    'res_id': invoice_ids[0],
                    'mimetype': 'application/pdf',
                })
                _logger.info(f"Attachment created: {attachment.name} (ID: {attachment.id})")

                # Prepare mail values
                subject = mail_template.subject or "Pending Invoice Summary"
                body_html = mail_template.body_html or "<p>Please find attached your pending invoice summary.</p>"

                mail_values = {
                    'subject': subject,
                    'body_html': body_html,
                    'email_to': customer.email,
                    'email_from': email_from,
                    'attachment_ids': [(4, attachment.id)],
                }
                
                # Create and send mail
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.send()
                sent_count += 1
                
                _logger.info(f"✓ Successfully sent pending invoice report to '{customer.name}' ({customer.email}). Mail ID: {mail.id}")

            except Exception as e:
                failed_count += 1
                import traceback
                error_details = traceback.format_exc()
                _logger.error(f"✗ Failed to send invoice report to '{customer.name}' (ID: {customer.id})")
                _logger.error(f"Error type: {type(e).__name__}")
                _logger.error(f"Error message: {str(e)}")
                _logger.error(f"Full traceback:\n{error_details}")
        
        _logger.info(f"Finished _cron_send_pending_invoice_report. Sent: {sent_count}, Failed: {failed_count}")
        return True