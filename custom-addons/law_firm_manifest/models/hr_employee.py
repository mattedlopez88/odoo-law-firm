from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_lawyer = fields.Boolean(
        string="Es abogado",
        help='Indica si este empleado ejerce como abogado.'
    )

    bar_number = fields.Char(
        string="Numero de registro(Colergio de abogados)"
    )

    law_role = fields.Selection(
        [
            ('partner', 'Socio'),
            ('director', 'Director Legal'),
            ('senior', 'Abogado Senior'),
            ('junior', 'Abogado Junior'),
            ('paralegal', 'Paralegal'),
            ('intern', 'Pasante'),
            ('assistant', 'Asistente / Secretaria'),
        ],
        string='Rol en la firma',
    )

    law_practice_area = fields.Selection(
        [
            ('civil', 'Civil'),
            ('penal', 'Penal'),
            ('laboral', 'Laboral'),
            ('tributario', 'Tributario'),
            ('corporativo', 'Corporativo'),
            ('familia', 'Familia'),
            ('otros', 'Otros'),
        ],
        string='Área de Práctica Principal',
    )