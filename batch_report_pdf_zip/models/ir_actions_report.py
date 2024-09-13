
import zipfile
import io
import base64
from odoo import models, fields, api
import logging

class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    
    is_zip = fields.Boolean(string="Download as ZIP", help="Generate one PDF per record and download them as a ZIP file")
