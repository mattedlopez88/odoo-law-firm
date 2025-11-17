{
    "name": "RealMatias",
    "version": "1.0",
    # "website": "https://www.matias.com",
    "description": """
        Real state by matias
    """,
    "category": "Sales",
    "depends": ["base"],
    "data":[
        'security/ir.model.access.csv',
        'views/property_view.xml',
        'views/property_tag_view.xml',
        'views/property_type_view.xml',
        'views/menu_items.xml'
    ],
    "author": "Matias lp",
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}