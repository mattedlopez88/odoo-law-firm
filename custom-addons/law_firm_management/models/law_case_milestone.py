from odoo import models, fields

class LawCaseMilestone(models.Model):
    _name = 'law.case.milestone'
    _description = 'Hito de Caso'

    case_id = fields.Many2one('law.case', requiered=True)
    name = fields.Char('Titulo', required=True)
    milestone_type = fields.Selection([
        ('audiencia', 'Audiencia'),
        ('demanda', 'Demanda'),
        ('contestacion', 'Contestacion'),
        ('inspeccion', 'Inspeccion'),
        ('negociacion', 'Negociacion'),
        ('sentencia', 'Sentincia'),
    ])
    notes = fields.Text('Notas')
    resultado = fields.Char('Resultado')