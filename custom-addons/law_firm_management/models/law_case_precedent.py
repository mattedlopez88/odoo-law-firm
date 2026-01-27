from odoo import api, models, fields

class LawCasePrecedent(models.Model):
    _name = 'law.case.precedent'
    _description = 'Precedente Legal'
    _order = 'decision_date desc, id desc'
    _rec_name = 'case_name'

    case_name = fields.Char(string='Nombre del caso', required=True, help="Ej: Smith vs. Jones, Sentencia 123-2025")
    reference_number = fields.Char(string="Numero de Referencia", help="Numero de expediente o sentencia")
    court = fields.Char(string="Corte/Tribunal", required=True, help="Ej: Corte Suprema de Justicia")
    decision_date = fields.Date(string="Fecha de Decision", required=True)

    favoured_party = fields.Selection([
        ('plaintiff', 'Demandante'),
        ('defendant', 'Demandado'),
    ], string="a Favor de", help="Parte a favor de la cual se emitio la decision")

    practice_area_id = fields.Many2one(
        'law.practice.area',
        string="Area de Practica"
    )

    legal_topic_ids = fields.Many2many(
        'law.legal.topic',
        string="Temas Legales",
        help="Temas especificos que trata este precedente"
    )

    legal_principle = fields.Text(string="Principio Legal", required=True, help="Principio o doctrina legal establecida")

    summary = fields.Text(string="Resumen del Caso", help="Resumen de los hechos y la decision")
    relevant_articles = fields.Text(string="Articulos Aplicables", help="Articulos de ley o codigo citados")
    url = fields.Char(string="Enlace/URL")
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Documentos Adjuntos",
        help="PDF de la sentencia, transcripciones, etc."
    )

    case_ids = fields.Many2many(
        'law.case',
        'law_case_precedent_rel',
        'precedent_id',
        'case_id',
        string="Casos de usan este Precedente"
    )

    usage_count = fields.Integer(compute='_compute_usage_count', string="Veces Citado", store=True)

    jurisdiction = fields.Selection([
        ('national', 'Nacional'),
        ('provincial', 'Provincial'),
        ('internacional', 'Internacional'),
    ], string="Jurisdicción")

    is_binding = fields.Boolean(string="Es Vinculante", help="Si el precendete es vinculante o persuasivo")

    active = fields.Boolean(default=True)
    notes= fields.Text(string="Notas Internas")

    @api.depends('case_ids')
    def _compute_usage_count(self):
        for precedent in self:
            precedent.usage_count = len(precedent.case_ids)
