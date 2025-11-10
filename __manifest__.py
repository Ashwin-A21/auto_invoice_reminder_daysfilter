{
    'name': 'Automatic Invoice Reminder ',
    'version': '1.7',
    'summary': 'Automatically send pending invoice report to customers weekly with days filter',
    'category': 'Accounting',
    'depends': ['account', 'mail', 'base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/invoice_pending_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Concept Solutions',
    'website': 'https://www.csloman.com',
}