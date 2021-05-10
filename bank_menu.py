from odoo import tools,fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
import base64

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

    def btn_import_file(self):
        self.ensure_one()
        if self.processed_file:
            raise ValidationError('Archivo ya procesado')
        if not self.statement_file:
            raise ValidationError('Debe ingresar el archivo')
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
                    raise ValidationError('%s'%(items[3]))
            else:
                amount = 0
            vals = {
                    'date': items[0],
                    'name': items[2],
                    'ref': items[1],
                    'amount': amount,
                    'statement_id': self.id,
                    }
            bank_line_id = self.env['account.bank.statement.line'].create(vals)
        self.processed_file = True

