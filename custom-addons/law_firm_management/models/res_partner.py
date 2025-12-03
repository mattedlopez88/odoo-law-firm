from odoo import api, models, fields
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cedula = fields.Char(string="Cédula", size=10)
    ruc = fields.Char(string="RUC", size=13)

    # Role flags
    is_client = fields.Boolean(string="Cliente", default=False)
    is_counterparty = fields.Boolean(string="Contraparte", default=False)
    is_witness = fields.Boolean(string="Testigo", default=False)
    is_expert = fields.Boolean(string="Perito", default=False)

    payment_reliability = fields.Selection([
        ('poor', 'Malo'),
        ('fair', 'Regular'),
        ('Good', 'Bueno'),
        ('excellent', 'Excelente'),
    ], string="Canfiabilidad de Pago")

    client_since = fields.Date(string="Cliente Desde")
    client_notes = fields.Text(string="Notas del Cliente")

    client_case_ids = fields.One2many(
        'law.case',
        'client_id',
        string="Casos como Cliente"
    )

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

    @api.depends('client_case_ids', 'client_case_ids.case_outcome')
    def _compute_case_stats(self):
        for partner in self:
            cases = partner.client_case_ids
            partner.case_count = len(cases)

            closed_cases = cases.filtered(lambda c: c.case_outcome)
            won = closed_cases.filtered(lambda c: c.case_outcome == 'won')
            lost = closed_cases.filtered(lambda c: c.case_outcome == 'lost')

            partner.cases_won = len(won)
            partner.cases_lost = len(lost)
            partner.success_rate = (len(won) / len(closed_cases) * 100) if closed_cases else 0.0

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
# from odoo import models, fields
#
# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     is_client = fields.Boolean(
#         string='Cliente',
#         default=False,
#         help='Marca si este contacto es un cliente de la firma.')
#     is_lawyer = fields.Boolean(
#         string='Abogado',
#         default=False,
#         help='Marca si este contacto es un abogado de la firma.')
#     bar_number = fields.Char(string="License Number")
#     cedula = fields.Char(string="Cedula")
#     ruc = fields.Char(string="RUC")
#     bar_number = fields.Char(string="License Number")
#     legal_area_ids = fields.Many2many(
#         'law.legal.area',string='Areas de Práctica',
#     )
#
#     law_client_type = fields.Selection([
#         ('persona', 'Persona Natural'),
#         ('empresa', 'Empresa')
#     ])
#
#     law_notes = fields.Text(
#         string='Notas Legales',
#         help='Notas adicionales relacionadas con el cliente legal.'
#     )
#
#     law_case_ids = fields.One2many(
#         'law.case',
#         'client_id',
#         string='Casos Legales'
#     )
