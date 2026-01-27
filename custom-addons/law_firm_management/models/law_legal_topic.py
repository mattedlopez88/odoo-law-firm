from odoo import models, fields

class LawLegalTopic(models.Model):
    _name = 'law.legal.topic'
    _description = 'Tema Legal'
    _order = 'name asc'

    name = fields.Char(required=True)
    code = fields.Char(string="Codigo")

    parent_id = fields.Many2one(
        'law.legal.topic',
        string="Tema Padre",
        ondelete = 'cascade'
    )

    child_ids = fields.One2many(
        'law.legal.topic',
        'parent_id',
        string="Sub-temas"
    )

    description = fields.Text()
    active = fields.Boolean(default=True)