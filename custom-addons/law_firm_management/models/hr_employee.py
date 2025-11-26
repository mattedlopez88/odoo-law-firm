from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_lawyer = fields.Boolean(string="Is Lawyer")
    lawyer_title = fields.Char(string="Title / Position")        # e.g. Partner, Associate
    practice_area = fields.Char(string="Main Practice Area")

    def action_view_law_cases(self):
        """
        Open a list of cases where this employee is the responsible lawyer.
        """
        self.ensure_one()
        action = self.env.ref('law_firm_management.action_law_case').read()[0]
        action['domain'] = [('responsible_employee_id', '=', self.id)]
        action['context'] = {'default_responsible_employee_id': self.id}
        return action
# from odoo import models, fields
#
# class HREmployee(models.Model):
#     _inherit = 'hr.employee'
#
#     is_lawyer = fields.Boolean(
#         string="Es abogado",
#         help='Indica si este empleado ejerce como abogado.'
#     )
#
#     bar_number = fields.Char(string="Numero de registro(Colegio de abogados)")
#
#     law_role = fields.Selection(
#         [
#             ('partner', 'Socio'),
#             ('director', 'Director Legal'),
#             ('senior', 'Abogado Senior'),
#             ('junior', 'Abogado Junior'),
#             ('paralegal', 'Paralegal'),
#             ('intern', 'Pasante'),
#             ('assistant', 'Asistente / Secretaria'),
#         ],
#         string='Rol en la firma',
#     )
#
#     hourly_rate = fields.Monetary(
#         string='Tarifa por Hora',
#         help='Tarifa por hora del abogado.'
#     )
#
#     law_practice_area = fields.Selection(
#         [
#             ('civil', 'Civil'),
#             ('penal', 'Penal'),
#             ('laboral', 'Laboral'),
#             ('tributario', 'Tributario'),
#             ('corporativo', 'Corporativo'),
#             ('familia', 'Familia'),
#             ('otros', 'Otros'),
#         ],
#         string='Área de Práctica Principal',
#     )