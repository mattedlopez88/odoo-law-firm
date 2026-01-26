{
    'name': 'Law Firm Management',
    'version': '1.1',
    'category': 'Services',
    'summary': 'Gestión interna de casos y empleados para firmas de abogados',
    'description': 'Módulo para manejar casos legales, roles, empleados y flujos internos.',
    'author': 'Matias Lopez',
    'depends': ['base', 'hr', 'mail', 'contacts'],
    'data': [
        'security/groups.xml',
        'security/security.xml',
        'security/ir.model.access.csv',

        'data/jobs.xml',
        'data/departments.xml',
        'data/law_case_sequence.xml',
        'data/law_practice_area_data.xml',
        # 'data/law_case_data.xml',
        # 'data/test_employees_data.xml',  # Mock employees/lawyers (must load before cases)
        # 'data/test_cases_data.xml',  # Mock test data for development/testing

        'views/res_partner_view.xml',
        'views/law_practice_area_views.xml',
        'views/law_case_precedent_views.xml',
        'views/law_case_stage_view.xml',
        'views/law_case_view.xml',
        'views/hr_employee_view.xml',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': True,
    "license": "LGPL-3",
}