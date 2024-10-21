# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import zipfile
from odoo.http import content_disposition
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import ReportController
from io import BytesIO
from datetime import datetime
import json


class ExtendedReportController(ReportController):

    @http.route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        doc_ids = []
        if docids:
            doc_ids = [int(i) for i in docids.split(',')]
        if converter == "zip" and report.is_zip and len(doc_ids) > 1:
            context = dict(request.env.context)
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            attachments = []
            for doc_id in doc_ids:
                pdf_content, _ = report.with_context(context).render_qweb_pdf(
                    [doc_id], data=data
                )
                pdf_name = f'{report.name}_{doc_id}.pdf'
                attachments.append((pdf_name, pdf_content))
            # Generate the ZIP file
            zip_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            bitIO = BytesIO()
            with zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_name, pdf_content in attachments:
                    zip_file.writestr(pdf_name, pdf_content)
            zip_content = bitIO.getvalue()
            headers = [
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', content_disposition(zip_filename))
            ]
            return request.make_response(
                zip_content,
                headers=headers
            )
        if converter == "zip" and report.report_type=="qweb-pdf":
            converter = "pdf"
        return super(ExtendedReportController, self).report_routes(
            reportname, docids, converter, **data
        )
