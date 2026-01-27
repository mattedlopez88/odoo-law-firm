from odoo import api, models, fields

class LegalArea(models.Model):
    _name = 'law.practice.area'
    _description = 'Area de Practica Legal'
    _order = 'sequence, name'

    name = fields.Char(string="Area",required=True, translate=True)
    code = fields.Char(string="Codigo", size=10, help="Codigo corto para identificar el area legal")
    sequence = fields.Integer(default=10, help="Order de Visualizacion")

    description = fields.Text(string='Descripción')
    color = fields.Integer(string="Color", help="Color para visualizacion en interfaz")

    parent_id = fields.Many2many(
        'law.practice.area',
        'law_practice_area_rel',
        'child_id',
        'parent_id',
        string="Area Padre",
        ondelete='cascade',
        help="Para sub-especialidades"
    )

    child_ids = fields.One2many(
        'law.practice.area',
        'parent_id',
        string="Sub-Areas"
    )

    case_count = fields.Integer(
        compute='_compute_case_count',
        string="Numero de Casos"
    )

    active_case_count = fields.Integer(
        compute='_compute_case_count',
        string="Casos Activos"
    )

    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notas Internas")

    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        for area in self:
            if area.parent_id:
                area.display_name = f"{area.parent_id.name}/{area.name}"
            else:
                area.display_name = area.name

    def _compute_case_count(self):
        for area in self:
            cases = self.env['law.case'].search([('practice_area_id', '=', area.id)])
            area.case_count = len(cases)
            area.active_case_count = len(cases.filtered(lambda c: c.state in ['draft', 'open']))