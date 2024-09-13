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

class ExtendedReportController(ReportController):

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        # Get the report
        report = request.env['ir.actions.report']._get_report_from_name(reportname)

        # Extend logic for ZIP generation when `is_zip` is enabled and converter is PDF
        if report.is_zip and converter == "pdf":
            context = dict(request.env.context)

            if docids:
                docids = [int(i) for i in docids.split(',')]

            # Handling context data passed
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])

            attachments = []
            for doc_id in docids:
                # Generate PDF for each document
                pdf_content, _ = report.with_context(context).render_qweb_pdf([doc_id], data=data)
                
                # Create attachment for each PDF
                attachment = request.env['ir.attachment'].create({
                    'name': f'{report.name}_{doc_id}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': report.model,
                    'res_id': doc_id,
                    'mimetype': 'application/pdf'
                })
                attachments.append(attachment)

            # Create a dictionary for storing file paths and names
            file_dict = {}
            for attachment in attachments:
                document = request.env[attachment.res_model].search([('id', '=', attachment.res_id)])
                document_name = f"[{document.name.replace('/', '_')}]" if document.name else ''
                date = f"[{datetime.today().strftime('%Y-%m-%d')}]"
                file_name = f"{document_name}{date}{attachment.name}"
                file_dict[f"{attachment.store_fname}:{file_name}"] = dict(
                    path=attachment._full_path(attachment.store_fname), name=file_name
                )

            # Generate the ZIP file
            zip_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            bitIO = BytesIO()
            zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
            for file_info in file_dict.values():
                zip_file.write(file_info['path'], file_info['name'])
            zip_file.close()
            
            # Return the ZIP file as the response
            return super(ExtendedReportController, self).report_routes(reportname, docids, converter, **data)

        # If not ZIP, call the parent method to handle standard behavior
        return super(ExtendedReportController, self).report_routes(reportname, docids, converter, **data)