from odoo import models, fields, api
from odoo.exceptions import UserError

class LawCase(models.Model):
    _name = 'law.case'
    _description = 'Caso Legal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Case Name",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Case Number",
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
    )

    client_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        tracking=True,
    )

    responsible_employee_id = fields.Many2one(
        'hr.employee',
        string="Abogado Responsable",
        domain=[('is_lawyer', '=', True)],
        tracking=True,
    )

    # lawyer_ids = fields.Many2many(
    #     'hr.employee',
    #     'law_case_lawyer_rel',
    #     'case_id',
    #     'employee_id',
    #     string="Equipo de Abogados",
    #     domain=[('is_lawyer', '=', True)],
    #     tracking=True,
    # )

    state = fields.Selection([
        ('draft', 'Draft / Intake'),
        ('open', 'Open'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed'),
    ], default='draft', string="Status", tracking=True)

    stage_id = fields.Many2one(
        'law.case.stage',
        string="Stage",
        tracking=True,
    )

    open_date = fields.Date(string="Open Date")
    close_date = fields.Date(string="Close Date")

    short_description = fields.Char(string="Short Description")
    facts = fields.Text(string="Case Notes / Facts")

    # --- decorators and functions ---

    @api.model
    def create(self, vals):
        for rec in vals:
            if not rec.get('code'):
                rec['code'] = self.env['ir.sequence'].next_by_code('law.case') or '/'
        return super().create(vals)

    def write(self, vals):
        result = super().write(vals)

        # for rec in vals:

        if 'stage_id' in vals:
            for case in self:
                if case.stage_id and case.stage_id.is_closed_stage:
                    case.state = 'closed'
                elif case.state == 'closed' and not case.stage_id.is_closed_stage:
                    # Reopening a case by moving it back to a non-closed stage
                    case.state = 'open'

        return result

    def action_set_to_draft(self):
        self.write({'state': 'draft', 'open_date': False, 'close_date': False})

    def action_open(self):
        for case in self:
            if not case.responsible_employee_id:
                raise UserError("Asignar un abogado responsable antes de abrir el caso.")
            case.state = 'open'
            case.open_date = fields.Date.today()

    def action_set_on_hold(self):
        self.write({'state': 'on_hold'})

    def action_close(self):
        for case in self:
            if case.state not in ('open', 'on_hold'):
                raise UserError("Only open or on-hold cases can be closed.")
            case.state = 'closed'
            case.close_date = fields.Date.today()

    def action_view_client(self):
        self.ensure_one()
        if not self.client_id:
            raise UserError("No client set on this case.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Client',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.client_id.id,
            'target': 'current',
        }
# from odoo import api, models, fields
# from odoo.exceptions import UserError
#
# class LawCase(models.Model):
#     _name = 'law.case'
#     _description = 'Caso Legal'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _order = 'create_date desc'
#
#     name = fields.Char('Título del Caso', required=True, tracking=True)
#     code = fields.Char('Case Number', readonly=True, copy=False, index=True)
#     reference_court = fields.Char(string='Referencia de Corte')
#     reference = fields.Char('Referencia Interna')
#
#     client_id = fields.Many2one(
#         'res.partner',
#         string='Cliente',
#         required=True,
#         domain=[('is_client', '=', True)],
#         tracking=True,
#     )
#     opponent_ids = fields.Many2many('res.partner', 'law_case_opponent_rel', 'case_id', 'partner_id', string="Contrapartes")
#     contact_person_id = fields.Many2one('res.partner', string="Contacto de la Empresa")  # if client is a company
#
#     responsible_lawyer_id = fields.Many2one('hr.employee',
#         string='Abogado Responsable',
#         domain=[('is_lawyer', '=', True)],
#         help='Abogado responsable principal del caso',
#     )
#
#     team_ids = fields.Many2many('hr.employee',
#         string='Equipo del Caso',
#         help='Abogados, paralegales o pasantes que participan en este caso',
#     )
#
#     assistant_ids = fields.Many2many('hr.employee', domain=[('is_assistant', '=', True)], string='Paralegales')
#     company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
#
#     type_id = fields.Many2one('law.case.type', string='Tipo de Caso', required=True)
#     practice_area_id = fields.Many2one('law.practice.area', string="Practice Area")
#     tag_ids = fields.Many2many('law.case.tag', string="Tags")
#     opening_date = fields.Date('Fecha de Apertura', default=fields.Date.today)
#     closing_date = fields.Date('Fecha de Cierre')
#
#     state = fields.Selection([
#         ('intake', 'Intake'),
#         ('review', 'In Review'),
#         ('open', 'In Progress'),
#         ('on_hold', 'On Hold'),
#         ('settled', 'Settled'),
#         ('won', 'Won'),
#         ('lost', 'Lost'),
#         ('closed', 'Closed'),
#     ], string="Estado", default='intake', tracking=True)
#
#     stage_id = fields.Many2one('law.case.stage', string="Stage", tracking=True)
#     priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High'), ('3', 'Critical')], string="Priority")
#
#     #dates
#     intake_date = fields.Date(string="Intake Date", default=fields.Date.context_today)
#     open_date = fields.Date(string="Fecha de Apertura")
#     close_date = fields.Date(string="Fecha de Cierre")
#     limitation_date = fields.Date(string="Statute of Limitations")
#
#     #descripcion/hechos
#     short_description = fields.Char(string="Descripción Breve")
#     facts = fields.Text(string="Hechos del Caso")
#     objective = fields.Text(string="Objetivo del Cliente")
#     strategy = fields.Text(string="Notas de Estrategia")
#
#     #financieros/ billing
#
#     # fee_type = fields.Selection([
#     #     ('hourly', 'Hourly'),
#     #     ('flat', 'Flat Fee'),
#     #     ('contingency', 'Contingency'),
#     #     ('retainer', 'Retainer'),
#     #     ('pro_bono', 'Pro Bono'),
#     # ], default='hourly', string="Fee Arrangement")
#     # hourly_rate = fields.Monetary(string="Case Hourly Rate")  # fallback
#     # flat_fee_amount = fields.Monetary()
#     # retainer_amount = fields.Monetary()
#     # currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
#     # analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
#     #
#
#     # # Relations with other entities
#
#     # hearing_ids = fields.One2many('law.case.hearing', 'case_id', string="Hearings")
#     # deadline_ids = fields.One2many('law.case.deadline', 'case_id', string="Deadlines")
#     # document_ids = fields.One2many('law.case.document', 'case_id', string="Documents")
#     # timesheet_ids = fields.One2many('law.case.timesheet', 'case_id', string="Time Entries")
#     # invoice_ids = fields.Many2many('account.move', string="Invoices", domain=[('move_type', '=', 'out_invoice')])
#     #
#     # total_hours = fields.Float(compute='_compute_billing', string="Total Hours", store=True)
#     # billable_amount = fields.Monetary(compute='_compute_billing', string="Billable Amount", store=True)
#     # amount_invoiced = fields.Monetary(compute='_compute_billing', string="Invoiced Amount", store=True)
#     # amount_to_invoice = fields.Monetary(compute='_compute_billing', string="To Invoice", store=True)
#     # description = fields.Text('Descripción del Caso')
#     # notes_internal = fields.Text('Notas Internas')
#
#     # Campos simples para tipo de caso y área
#     # practice_area = fields.Selection(
#     #     [
#     #         ('civil', 'Civil'),
#     #         ('penal', 'Penal'),
#     #         ('laboral', 'Laboral'),
#     #         ('tributario', 'Tributario'),
#     #         ('corporativo', 'Corporativo'),
#     #         ('familia', 'Familia'),
#     #         ('otros', 'Otros'),
#     #     ],
#     #     string='Área de Práctica',
#     # )
#
#     case_type = fields.Selection(
#         [
#             ('consulta', 'Consulta'),
#             ('patrocinio', 'Patrocinio'),
#             ('contrato', 'Contrato'),
#             ('litigio', 'Litigio'),
#         ],
#         string='Tipo de Caso',
#     )
#
#     active = fields.Boolean('Activo', default=True)
#
#     # @api.model
#     # def create(self, vals):
#     #     if not vals.get('code'):
#     #         vals['code'] = self.env['ir.sequence'].next_by_code('law.case') or '/'
#     #     return super().create(vals)
#
#     def action_open(self):
#         for case in self:
#             if not case.responsible_lawyer_id:
#                 raise UserError("You must assign a responsible lawyer before opening the case.")
#             case.state = 'open'
#             case.open_date = fields.Date.today()
#
#     def action_set_on_hold(self):
#         self.write({'state': 'on_hold'})
#
#     def action_close(self):
#         for case in self:
#             if case.state not in ('open', 'on_hold'):
#                 raise UserError("Only open or on-hold cases can be closed.")
#             case.state = 'closed'
#             case.close_date = fields.Date.today()
#
# # class LawCaseType(models.Model):
# #     _name = 'law.case.type'
# #     _description = 'Tipo de Caso Legal'
# #
# #     name = fields.Char(required=True)
# #     code = fields.Char()
# #     # default_fee_type = fields.Selection([...])
# #     default_practice_area_id = fields.Many2one('law.practice.area')
# #
# # class LawCaseTag(models.Model):
# #     _name = 'law.case.tag'
# #     _description = 'Case Tag'
# #     name = fields.Char(required=True)
# #     color = fields.Integer()
# #
# # class LawCaseStage(models.Model):
# #     _name = 'law.case.stage'
# #     _description = 'Case Stage'
# #     _order = 'sequence, id'
# #
# #     name = fields.Char(required=True)
# #     sequence = fields.Integer(default=10)
# #     fold = fields.Boolean(string="Folded in Kanban")
# #     is_closed = fields.Boolean(string="Closing Stage")
# #     state = fields.Selection([...])  # could sync with law.case.state