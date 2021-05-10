from odoo import tools,fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
import base64
import xlrd
import tempfile
import binascii

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def _compute_total_processed(self):
        for rec in self:
            res = 0
            for line in rec.line_ids:
                res = res + line.amount
            rec.total_processed = res

    statement_file = fields.Binary('Archivo Resumen')
    processed_file = fields.Boolean('Archivo procesado?')
    delimiter = fields.Char('Delimitador',default=',')
    total_processed = fields.Float('Total procesado',compute=_compute_total_processed)
    xls_or_csv = fields.Selection(selection=[('csv','CSV'),('xls','XLS')],string='CSV o Excel',default='xls')

    def btn_import_file(self):
        self.ensure_one()
        if self.processed_file:
            raise ValidationError('Archivo ya procesado')
        if not self.statement_file:
            raise ValidationError('Debe ingresar el archivo')
        if self.xls_or_csv == 'csv':
            self.process_csv_file()
        else:
            self.process_xls_file()

    def process_xls_file(self):
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.statement_file)) # self.xls_file is your binary field
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no > 0:
                vals = {
                    'date': xlrd.xldate_as_datetime(sheet.cell_value(row_no,0),0),
                    'name': sheet.cell_value(row_no,1),
                    'payment_ref': sheet.cell_value(row_no,2),
                    'amount': float(sheet.cell_value(row_no,3)),
                    'statement_id': self.id,
                    }
                bank_line_id = self.env['account.bank.statement.line'].create(vals)




    def process_csv_file(self):
        text_content = base64.b64decode(self.statement_file)
        text_lines = str(text_content).split('\\n')
        for i,text_line in enumerate(text_lines):
            if i < 1:
                continue
            items = text_line.split(self.delimiter)
            if len(items) < 4:
                continue
            not_lines = ['','\\r']
            if items[3].strip() not in not_lines:
                try:
                    amount = float(items[3].replace('\\r',''))
                except:
                    #raise ValidationError('%s'%(items[3]))
                    continue
            else:
                amount = 0
            vals = {
                    'date': items[0],
                    'name': items[2],
                    'payment_ref': items[1],
                    'amount': amount,
                    'statement_id': self.id,
                    }
            try:
                bank_line_id = self.env['account.bank.statement.line'].create(vals)
            except:
                import pdb;pdb.set_trace()
        self.processed_file = True

