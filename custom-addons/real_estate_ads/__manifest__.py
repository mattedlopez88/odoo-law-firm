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
        'views/property_offer_view.xml',
        'views/menu_items.xml',

        # Data Files
        'data/estate.property.type.csv',
        'data/estate.property.tag.csv',
        # 'data/property_type.xml',
        # 'data/property_tags.xml'
    ],
    "demo": [
        'demo/property_tag.xml',
    ],
    "author": "Matias lp",
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}