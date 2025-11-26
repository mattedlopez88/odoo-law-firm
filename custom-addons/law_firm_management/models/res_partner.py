from odoo import api, models, fields
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # external contact roles for the law firm context
    cedula = fields.Char(string="Cédula", required=True, size=10)
    is_law_client = fields.Boolean(string="Law Firm Client")
    is_law_external_party = fields.Boolean(string="External Party (Non-Client)")

    def action_view_law_cases(self):
        self.ensure_one()
        action = self.env.ref('law_firm_management.action_law_case').read()[0]
        action['domain'] = [('client_id', '=', self.id)]
        action['context'] = {'default_client_id': self.id}
        return action

    @api.constrains
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
