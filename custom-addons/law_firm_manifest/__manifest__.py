{
    'name': 'Law Firm Management',
    'version': '1.1',
    'category': 'Sales',
    'summary': 'Gestión interna de casos y empleados para firmas de abogados',
    'description': 'Módulo para manejar casos legales, roles, empleados y flujos internos.',
    'author': 'Matias Lopez',
    'depends': ["base", "hr", "mail"],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'data/jobs.xml',

        'views/res_partner_view.xml',
        'views/law_case_view.xml',
        'views/hr_employee_view.xml',

        'views/menu_items.xml',
    ],
    'installable': True,
    'application': True,
    "license": "LGPL-3",
}