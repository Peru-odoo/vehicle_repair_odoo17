# -*- coding: utf-8 -*-
{
    'name': "Vehicle Repair",
    'version': '17.0.1.0.0',
    'depends': ['base', 'fleet', 'hr_hourly_cost', 'product', 'stock', 'sale', 'account'],
    'category': '',
    'description': """
    summary of this app
    """,
    'data': ['security/repair_security.xml',
             'security/ir.model.access.csv',

             'report/vehicle_repair_template.xml',
             'report/report.xml',

             'data/ir_sequence_data.xml',
             'data/vehicle_type_data.xml',
             'data/labour_cost_product.xml',
             'data/mail_template.xml',
             'data/records_data.xml',
             'data/automation_service.xml',
             'data/website_menu.xml',

             'wizard/repair_wizard_views.xml',
             'views/snippets/snippet_views.xml',
             'views/repair_tag_views.xml',
             'views/customer_form_view.xml',
             'views/vehicle_repair_views.xml',
             'views/menu.xml',
             'views/repair_form_views.xml',
             'views/thanks_form_views.xml',
             'views/error_form_views.xml',
             'views/customer_form_views.xml',
             'views/snippets/record_details.xml',

             ],
    'assets':{
        'web.assets_backend': [
            'vehicle_repair/static/src/js/action_manager.js'
        ],
        'web.assets_frontend': [
            'vehicle_repair/static/src/xml/latest_repair.xml',
            'vehicle_repair/static/src/js/snippet.js',
        ],
    },
    # 'demo': ['data/ir_sequence_data.xml'],
    'application': 'True',
    'installable': True,
}
