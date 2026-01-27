from odoo import models, fields

class LawCaseWitness(models.Model):
    _name = 'law.case.witness'
    _description = 'Testigos del Caso'

    name = fields.Char(string="Nombre")
    case_id = fields.Many2one('law.case', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', requiered=True, string="Contacto")

    witness_type = fields.Selection([
        ('eyewitness', 'Testigo Presencial'),
        ('expert', 'Perito'),
        ('character', 'Testigo de Caracter'),
    ])

    credibility = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ])

    testimony_summary = fields.Text(string="Resumen del Testimonio")
    deposition_date = fields.Date(string="Fecha de Declaracion")
    is_hostile = fields.Boolean(string="Testigo Hostil")
    notes = fields.Text(string="Notas Internas")