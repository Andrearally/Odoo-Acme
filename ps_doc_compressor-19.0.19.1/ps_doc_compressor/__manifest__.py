# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) PySquad Informetics (<https://www.pysquad.com/>).
#
#    For Module Support : contact@pysquad.com
#
##############################################################################

{
    # Module Information
    "name": "Document Compressor",
    "version": "19.1",
    "category": "custom",
    "description": "Compress the large size of Image and Pdf Documnet",
    "summary": """
            Compress the Large size of Image and PDF documents once in a day
            """,

    # Author
    "author": "Pysquad Informatics LLP",
    "website": "https://www.pysquad.com",
    "license": "LGPL-3",

    # Dependencies
    "depends": ["base", ],

    # Data File
    "data": [
        'data/cron_job.xml',
        'views/attachement_view.xml',
    ],
    'images': [
        'static/description/banner_image.png',
    ],

    # Technical Specif.
    'installable': True,
    'application': False,
    'auto_install': False,

    # Other Info
    'price': 10,
    'currency': 'EUR'
}
