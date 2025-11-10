{
    'name': 'Automatic Invoice Reminder (Days Filter Only)',
    'version': '1.6',  # Changed from 1.5
    'summary': 'Automatically send pending invoice report to customers weekly with days filter',
    'category': 'Accounting',
    'depends': ['account', 'mail', 'base', 'web'],
    'data': [
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'data/invoice_pending_template.xml',  # <-- FILE PATH HAS CHANGED
    ],
    'installable': True,
    'application': False,
    'author': 'Concept Solutions ',
    'website': 'https://www.csloman.com',
}