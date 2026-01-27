from odoo import api, models, fields
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # cedula = fields.Char(string="Cédula", size=10)
    # ruc = fields.Char(string="RUC", size=13)

    # Role flags
    # is_client = fields.Boolean(string="Cliente", default=False)
    is_counterparty = fields.Boolean(string="Contraparte", default=False)
    is_witness = fields.Boolean(string="Testigo", default=False)
    is_expert = fields.Boolean(string="Perito", default=False)

    counterparty_case_ids = fields.One2many(
        'law.case',
        'counterparty_id',
        string="Casos como Contraparte"
    )

    witness_case_ids = fields.Many2many(
        'law.case',
        'law_Case_witness_rel',
        'partner_id',
        'case_id',
        string="Casos como Testigo"
    )

    expert_case_ids = fields.Many2many(
        'law.case',
        'law_case_expert_rel',
        'partner_id',
        'case_id',
        string="Casos como Perito"
    )

    # Statistics
    case_count = fields.Integer(compute='_compute_case_stats', string="Total de Casos")
    case_won = fields.Integer(compute='_compute_case_stats', string="Casos Ganados")
    case_lost = fields.Integer(compute='_compute_case_stats', string="Casos Perdidos")
    success_rate = fields.Float(compute='_compute_case_stats', string="Tasa de Éxito (%)")

    counterparty_count = fields.Integer(compute='_compute_counterparty_stats', string="Veces como contraparte")
    counterparty_win_rate = fields.Float(compute='_compute_counterparty_stats', string="Victorias como contraparte (%)")

    # @api.depends('client_case_ids', 'client_case_ids.case_outcome')
    # def _compute_case_stats(self):
    #     for partner in self:
    #         cases = partner.client_case_ids
    #         partner.case_count = len(cases)
    #
    #         closed_cases = cases.filtered(lambda c: c.case_outcome)
    #         won = closed_cases.filtered(lambda c: c.case_outcome == 'won')
    #         lost = closed_cases.filtered(lambda c: c.case_outcome == 'lost')
    #
    #         partner.cases_won = len(won)
    #         partner.cases_lost = len(lost)
    #         partner.success_rate = (len(won) / len(closed_cases) * 100) if closed_cases else 0.0

    @api.depends('counterparty_case_ids', 'counterparty_case_ids.case_outcome')
    def _compute_counterparty_stats(self):
        for partner in self:
            cases = partner.counterparty_case_ids
            partner.counterparty_count = len(cases)

            closed_cases = cases.filtered(lambda c: c.case_outcome)
            they_won = closed_cases.filtered(lambda c: c.case_outcome == 'lost')

            partner.counterparty_win_rate = (len(they_won) / len(closed_cases) * 100) if closed_cases else 0.0


    def action_view_law_cases(self):
        self.ensure_one()
        action = self.env.ref('law_firm_management.action_law_case').read()[0]
        domain = ['|', '|',
                    ('client_id', '=', self.id),
                    ('counterparty_id', '=', self.id),
                    ('witness_ids', 'in', self.id)]
        action['domain'] = domain
        action['context'] = {'default_client_id': self.id}
        return action

    @api.constrains('cedula')
    def _check_cedula(self):
        for partner in self:
            if partner.cedula and len(partner.cedula) != 10:
                raise ValidationError("La cédula debe tener 10 caracteres.")
