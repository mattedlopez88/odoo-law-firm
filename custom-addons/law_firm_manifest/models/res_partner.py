from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_law_client = fields.Boolean(
        string='Cliente de la Firma',
        default=False,
        help='Marca si este contacto es un cliente de la firma de abogados.')

    law_client_type = fields.Selection([
        ('persona', 'Persona Natural'),
        ('empresa', 'Empresa')
    ])

    law_notes = fields.Text(
        string='Notas Legales',
        help='Notas adicionales relacionadas con el cliente legal.'
    )

    law_case_ids = fields.One2many(
        'law.case',
        'client_id',
        string='Casos Legales'
    )
