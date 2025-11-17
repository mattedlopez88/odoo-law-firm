from odoo import models, fields

class LawCase(models.Model):
    _name = 'law.case'
    _description = 'Caso Legal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Título del Caso', required=True)
    reference = fields.Char('Referencia Interna')
    client_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        domain=[('is_law_client', '=', True)],
        tracking=True,
    )

    client_name = fields.Char(
        string='Nombre del Cliente',
        tracking=True,
    )
    client_contact = fields.Char('Contacto del Cliente')

    responsible_id = fields.Many2one('hr.employee',
        string='Abogado Responsable',
        help='Abogado responsable principal del caso',
    )

    team_ids = fields.Many2many('hr.employee',
        string='Equipo del Caso',
        help='Abogados, paralegales o pasantes que participan en este caso',
    )

    opening_date = fields.Date('Fecha de Apertura', default=fields.Date.today)
    closing_date = fields.Date('Fecha de Cierre')

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('in_progress', 'En curso'),
            ('on_hold', 'En espera'),
            ('closed', 'Cerrado'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        required=True,
    )

    description = fields.Text('Descripción del Caso')
    notes_internal = fields.Text('Notas Internas')

    # Campos simples para tipo de caso y área
    practice_area = fields.Selection(
        [
            ('civil', 'Civil'),
            ('penal', 'Penal'),
            ('laboral', 'Laboral'),
            ('tributario', 'Tributario'),
            ('corporativo', 'Corporativo'),
            ('familia', 'Familia'),
            ('otros', 'Otros'),
        ],
        string='Área de Práctica',
    )

    case_type = fields.Selection(
        [
            ('consulta', 'Consulta'),
            ('patrocinio', 'Patrocinio'),
            ('contrato', 'Contrato'),
            ('litigio', 'Litigio'),
        ],
        string='Tipo de Caso',
    )

    active = fields.Boolean('Activo', default=True)