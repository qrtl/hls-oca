import zipfile
import io
import base64
from odoo.http import content_disposition
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import ReportController
from io import BytesIO
from datetime import datetime
import ast
import logging
import json

class ExtendedReportController(ReportController):

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        # Extend logic for ZIP generation when `is_zip` is enabled and converter is PDF
        if report.is_zip and converter == "pdf":
            context = dict(request.env.context)
            doc_ids = []
            if docids:
                doc_ids = [int(i) for i in docids.split(',')]

            # Handling context data passed
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            attachments = []
            for doc_id in doc_ids:
                # Generate PDF for each document
                pdf_content, _ = report.with_context(context).render_qweb_pdf([doc_id], data=data)
                pdf_name = f'{report.name}_{doc_id}.pdf'
                attachments.append((pdf_name, pdf_content))
            # Generate the ZIP file
            zip_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            bitIO = BytesIO()
            with zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_name, pdf_content in attachments:
                    zip_file.writestr(pdf_name, pdf_content)
            try:
                zip_content = bitIO.getvalue()
                content_length = len(zip_content)
                logging.info(f"ZIP file size: {content_length} bytes")
                return request.make_response(
                    zip_content,
                    headers=[('Content-Type', 'application/x-zip-compressed'), ('Content-Disposition', content_disposition(zip_filename))]
                )
            except Exception as e:
                logging.exception("Error generating or returning ZIP file: %s", str(e))
                return request.make_response("An error occurred while generating the ZIP file.", 500)
        return super(ExtendedReportController, self).report_routes(reportname, docids, converter, **data)
