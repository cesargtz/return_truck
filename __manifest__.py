# -*- coding: utf-8 -*-
{
    'name': "return_truck",

    'summary': """
        Devuelve el producto exedente del productor""",

    'description': """
        Refresa el producto al productor mediante salida de camión siguiendo el proceso de la empresa.
    """,

    'author': "Yecora",
    'website': "yecora.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','vehicle_reception'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/return_truck.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
