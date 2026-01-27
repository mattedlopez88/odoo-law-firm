from odoo import models, fields

class LawCaseEvidence(models.Model):
    _name = 'law.case.evidence'
    _description = 'Evidencia del Caso'
    _order = 'sequence, id'

    case_id = fields.Many2one('law.case', required=True)
    sequence = fields.Integer(default=10)

    name = fields.Char(string="Descripción",required=True)
    evidence_type = fields.Selection([
        ('document', 'Documento'),
        ('physical', 'Evidencia Fisica'),
        ('testimony', 'Testimonio'),
        ('digital', 'Evidencia Digital'),
        ('expert', 'Peritaje'),
        ('photo', 'Fotografia'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ], required=True)

    quality = fields.Selection([
        ('weak', 'Debil'),
        ('moderate', 'Moderada'),
        ('strong', 'Fuerte'),
        ('decisive', 'Decisiva'),
    ], string="Calidad")

    admissibility = fields.Selection([
        ('admissible', 'Admisible'),
        ('questionable', 'Cuestionable'),
        ('inadmisible', 'Inadmisible'),
    ], string="Admisibilidad")

    obtained_date = fields.Date(string="Fecha de Obtencion")
    notes = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string="Archivos")
