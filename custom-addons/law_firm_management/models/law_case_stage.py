from odoo import models, fields

class LawCaseStage(models.Model):
    _name = 'law.case.stage'
    _description = 'Law Case Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(
        string="Folded in Kanban",
        help="If true, the column appears collapsed in Kanban views."
    )
    is_closed_stage = fields.Boolean(
        string="Closing Stage",
        help="When a case reaches this stage, mark it as closed."
    )
    description = fields.Text()