from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LawClient(models.Model):
    _name = 'law.client'
    _description = 'Law Firm Client'
    # _inherit = ['res.partner']
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner',
        string='Related Partner',
        required=True,
        ondelete='cascade',
        help='Link to the base partner record'
    )

    # Client identification
    cedula = fields.Char(
        string="Cédula",
        size=10,
        required=True,
        index=True,
        help='Client national ID (10 digits)'
    )

    ruc = fields.Char(
        string="RUC",
        size=13,
        help='Tax identification number (13 digits for companies)'
    )

    client_type = fields.Selection([
        ('natural', 'Persona Natural'),
        ('juridical', 'Persona Jurídica')
    ], string='Tipo de Cliente', default='natural', required=True)

    # Client status
    client_status = fields.Selection([
        ('prospect', 'Prospecto'),
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('blacklisted', 'Lista Negra')
    ], string='Estado del Cliente', default='prospect', tracking=True)

    client_since = fields.Date(
        string="Cliente Desde",
        default=fields.Date.today,
        help='Date when the client was registered'
    )

    # Payment information
    payment_reliability = fields.Selection([
        ('poor', 'Malo'),
        ('fair', 'Regular'),
        ('good', 'Bueno'),
        ('excellent', 'Excelente'),
    ], string="Confiabilidad de Pago")

    # payment_terms = fields.Many2one(
    #     'account.payment.term',
    #     string='Términos de Pago'
    # )

    credit_limit = fields.Monetary(
        string='Límite de Crédito',
        currency_field='currency_id'
    )

    # Relationships
    case_ids = fields.One2many(
        'law.case',
        'client_id',
        string='Casos',
        help='Cases where this client is involved'
    )

    # Statistics
    case_count = fields.Integer(
        compute='_compute_case_stats',
        string='Total de Casos',
        store=True
    )

    active_case_count = fields.Integer(
        compute='_compute_case_stats',
        string='Casos Activos',
        store=True
    )

    closed_case_count = fields.Integer(
        compute='_compute_case_stats',
        string='Casos Cerrados',
        store=True
    )

    cases_won = fields.Integer(
        compute='_compute_case_stats',
        string='Casos Ganados',
        store=True
    )

    cases_lost = fields.Integer(
        compute='_compute_case_stats',
        string='Casos Perdidos',
        store=True
    )

    success_rate = fields.Float(
        compute='_compute_case_stats',
        string='Tasa de Éxito (%)',
        store=True
    )

    total_billed = fields.Monetary(
        compute='_compute_financial_stats',
        string='Total Facturado',
        currency_field='currency_id'
    )

    total_paid = fields.Monetary(
        compute='_compute_financial_stats',
        string='Total Pagado',
        currency_field='currency_id'
    )

    outstanding_balance = fields.Monetary(
        compute='_compute_financial_stats',
        string='Saldo Pendiente',
        currency_field='currency_id'
    )

    # Notes and documentation
    client_notes = fields.Text(string='Notas del Cliente')

    internal_notes = fields.Text(
        string='Notas Internas',
        help='Internal notes not visible to client'
    )

    special_requirements = fields.Text(
        string='Requerimientos Especiales',
        help='Any special requirements or considerations for this client'
    )

    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('case_ids', 'case_ids.state', 'case_ids.case_outcome')
    def _compute_case_stats(self):
        """Compute case statistics for the client"""
        for client in self:
            cases = client.case_ids
            client.case_count = len(cases)

            # Count by state
            client.active_case_count = len(cases.filtered(
                lambda c: c.state in ['draft', 'open', 'on_hold']
            ))
            client.closed_case_count = len(cases.filtered(
                lambda c: c.state == 'closed'
            ))

            # Count by outcome
            closed_cases = cases.filtered(lambda c: c.case_outcome)
            won_cases = closed_cases.filtered(lambda c: c.case_outcome == 'won')
            lost_cases = closed_cases.filtered(lambda c: c.case_outcome == 'lost')

            client.cases_won = len(won_cases)
            client.cases_lost = len(lost_cases)

            # Calculate success rate
            if closed_cases:
                client.success_rate = (len(won_cases) / len(closed_cases)) * 100
            else:
                client.success_rate = 0.0

    @api.depends('case_ids')
    def _compute_financial_stats(self):
        """Compute financial statistics for the client"""
        for client in self:
            # TODO: Implement when billing/invoicing module is added
            client.total_billed = 0.0
            client.total_paid = 0.0
            client.outstanding_balance = 0.0

    @api.constrains('cedula')
    def _check_cedula(self):
        """Validate cedula format"""
        for client in self:
            if client.cedula:
                # Remove any non-digit characters
                cedula_clean = ''.join(filter(str.isdigit, client.cedula))

                if len(cedula_clean) != 10:
                    raise ValidationError('La cédula debe tener exactamente 10 dígitos.')

                # Check for duplicate cedula
                duplicate = self.search([
                    ('cedula', '=', client.cedula),
                    ('id', '!=', client.id)
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        f'Ya existe un cliente con la cédula {client.cedula}: {duplicate.name}'
                    )

    @api.constrains('ruc')
    def _check_ruc(self):
        """Validate RUC format"""
        for client in self:
            if client.ruc:
                # Remove any non-digit characters
                ruc_clean = ''.join(filter(str.isdigit, client.ruc))

                if len(ruc_clean) != 13:
                    raise ValidationError('El RUC debe tener exactamente 13 dígitos.')

                # Check for duplicate RUC
                duplicate = self.search([
                    ('ruc', '=', client.ruc),
                    ('id', '!=', client.id)
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        f'Ya existe un cliente con el RUC {client.ruc}: {duplicate.name}'
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle partner creation"""
        for vals in vals_list:
            # Create partner if not provided
            if 'partner_id' not in vals:
                partner_vals = {
                    'name': vals.get('name', 'Cliente'),
                    'company_type': 'company' if vals.get('client_type') == 'juridical' else 'person',
                }
                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id

        return super(LawClient, self).create(vals_list)

    def write(self, vals):
        """Override write to handle updates"""
        # Ensure is_client remains True
        # if 'is_client' in vals:
        #     vals['is_client'] = True

        return super(LawClient, self).write(vals)

    def action_view_cases(self):
        """Open a list of cases for this client"""
        self.ensure_one()

        return {
            'name': f'Casos de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'law.case',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.partner_id.id)],
            'context': {
                'default_client_id': self.partner_id.id,
                'search_default_active': 1,
            },
        }

    def action_view_active_cases(self):
        """Open a list of active cases for this client"""
        self.ensure_one()

        return {
            'name': f'Casos Activos de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'law.case',
            'view_mode': 'list,form',
            'domain': [
                ('client_id', '=', self.id),
                ('state', 'in', ['draft', 'open', 'on_hold'])
            ],
            'context': {'default_client_id': self.id},
        }

    def action_create_case(self):
        """Create a new case for this client"""
        self.ensure_one()

        return {
            'name': 'Nuevo Caso',
            'type': 'ir.actions.act_window',
            'res_model': 'law.case',
            'view_mode': 'form',
            'context': {
                'default_client_id': self.partner_id.id,
            },
            'target': 'current',
        }

    def action_set_active(self):
        """Set client status to active"""
        self.write({'client_status': 'active'})

    def action_set_inactive(self):
        """Set client status to inactive"""
        self.write({'client_status': 'inactive'})

    def action_blacklist(self):
        """Add client to blacklist"""
        self.write({'client_status': 'blacklisted'})

    def name_get(self):
        """Override name_get to show cedula in name"""
        result = []
        for client in self:
            name = client.name
            if client.cedula:
                name = f'{name} [{client.cedula}]'
            result.append((client.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Override search to allow searching by cedula"""
        args = args or []

        if name:
            # Search by name or cedula
            domain = ['|', ('name', operator, name), ('cedula', operator, name)]
            if operator in ('=', '!='):
                # Exact match on RUC as well
                domain = ['|', '|', ('name', operator, name),
                         ('cedula', operator, name), ('ruc', operator, name)]
        else:
            domain = []

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
