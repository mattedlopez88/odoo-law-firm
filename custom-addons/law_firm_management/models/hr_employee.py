from odoo import api, models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_lawyer = fields.Boolean(string="Es Abogado", default=True)

    years_of_experience = fields.Integer(string="Años de Experiencia", default=0)
    expert_practice_area_ids = fields.Many2many(
        'law.practice.area',
        string="Áreas de Especialización",
    )

    lawyer_title = fields.Char(string="Titulo")
    practice_area = fields.Many2one(
        'law.practice.area',
        string="Área de Práctica",
    )

    case_count = fields.Integer(compute='_compute_case_count')

    @api.depends()
    def _compute_case_count(self):
        for employee in self:
            employee.case_count = self.env['law.case'].search_count([
                ('responsible_employee_id', '=', employee.id),
                ('state', 'in', ['draft', 'open', 'in_progress'])
            ])

    def action_view_law_cases(self):
        """
        Open a list of cases where this employee is the responsible lawyer.
        """
        self.ensure_one()
        action = self.env.ref('law_firm_management.action_law_case').read()[0]
        action['domain'] = [('responsible_employee_id', '=', self.id)]
        action['context'] = {'default_responsible_employee_id': self.id}
        return action