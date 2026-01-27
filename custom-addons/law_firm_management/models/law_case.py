from odoo import models, fields, api
from odoo.exceptions import UserError
from ..services.case_success_rate_service import CaseSuccessRateService
from ..services.case_validation_service import CaseValidationService
from ..services.precedent_analysis_service import PrecedentAnalysisService
from ..services.case_state_service import CaseStateMachine
import logging

_logger = logging.getLogger(__name__)

class LawCase(models.Model):
    _name = 'law.case'
    _description = 'Caso Legal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string="Nombre del Caso", required=True, tracking=True)

    code = fields.Char(
        string="Numero de Caso",
        readonly=True, copy=False, index=True, tracking=True)

    client_id = fields.Many2one(
        'law.client',
        string="Cliente", required=True, tracking=True)
        # domain=[('is_client', '=', True)])

    client_role = fields.Selection([
        ('plaintiff', 'Demandante'),
        ('defendant', 'Demandado'),
    ], string="Rol", tracking=True)

    counterparty_id = fields.Many2one(
        'res.partner',
        string="Contraparte", tracking=True,
        domain=[('is_counterparty', '=', True)],
    )

    @api.depends('client_role')
    def _compute_counterparty_role(self):
        for case in self:
            if case.client_role == 'plaintiff':
                case.counterparty_role = 'defendant'
            elif case.client_role == 'defendant':
                case.counterparty_role = 'plaintiff'
            else:
                case.counterparty_role = False

    counterparty_role = fields.Selection([
        ('plaintiff', 'Demandante'),
        ('defendant', 'Demandado'),
    ], compute='_compute_counterparty_role',
        string="Rol de la Contraparte",
        tracking=True)

    responsible_employee_id = fields.Many2one(
        'hr.employee',
        string="Abogado Responsable", domain=[('is_lawyer', '=', True)], tracking=True)

    responsible_user_id = fields.Many2one(
        'res.users',
        string='Usuario responsable',
        related='responsible_employee_id.user_id',
        store=True, tracking=True, index=True,
    )

    team_user_ids = fields.Many2many(
        'res.users',
        string='Usuarios del Equipo',
        compute='_compute_team_user_ids',
        store=True,
        compute_sudo=True,
        readonly=True,
    )

    @api.depends('lawyer_ids.user_id')
    def _compute_team_user_ids(self):
        for case in self:
            case.team_user_ids = case.lawyer_ids.mapped('user_id')

    case_strength = fields.Selection([
        ('very_weak', 'Muy Débil'),
        ('weak', 'Débil'),
        ('moderate', 'Moderado'),
        ('strong', 'Fuerte'),
        ('very_strong', 'Muy Fuerte'),
    ], string="Fortaleza del Caso", tracking=True)

    case_complexity = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('very_high', 'Muy Alta'),
    ], string="Complejidad del Caso", tracking=True)

    estimated_success_rate = fields.Float(string="Tasa de Exito", compute='_compute_success_rate', store=True, tracking=True)

    risk_level = fields.Selection([
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('critical', 'Crítico'),
    ], string="Nivel de Riesgo", tracking=True)

    evidence_strength = fields.Selection([
        ('weak', 'Débil'),
        ('moderate', 'Moderada'),
        ('strong', 'Fuerte'),
        ('conclusive', 'Concluyente'),
    ], string="Calidad de Evidancias")

    evidence_ids = fields.One2many('law.case.evidence', 'case_id', string='Evidencias')
    witness_ids = fields.One2many('law.case.witness', 'case_id', string="Testigos")

    precedents_ids = fields.Many2many(
        'law.case.precedent',
        'law_case_precedent_rel',
        'case_id',
        'precedent_id',
        string="Precedentes Legales",
        help='Precedentes Legales Relacionados con este Caso'
    )

    has_favorable_precedents = fields.Boolean(string="Tiene Precedentes Favorables", compute='_compute_precedent_analysis', store=True)
    favorable_precedents_count = fields.Integer(compute='_compute_precedent_analysis', store=True)
    unfavorable_precedents_count = fields.Integer(compute='_compute_precedent_analysis', store=True, string="Numero de precedentes desfavorables")

    estimated_amount_claim = fields.Monetary(string="Monto Reclamado", currency_field='currency_id')
    estimated_amount_recovery = fields.Monetary(string="Recuperacion Estimada", currency_field='currency_id')
    estimated_legal_costs = fields.Monetary(string="Costos Legales Estiamdos", currency_field='currency_id')
    estimated_duration_months = fields.Integer(string="Duracion Estimada (Meses)")

    case_outcome = fields.Selection([
        ('won', 'Ganado'),
        ('lost', 'Perdido'),
        ('settled', 'Acuerdo'),
        ('dismissed', 'Desestimado'),
        ('withdrawn', 'Retirado'),
    ], string="Resultado Final", tracking=True)

    available_precedents = fields.Many2many(
        'law.case.precedent',
        'law_case_available_precedent_rel',
        'case_id',
        'precedent_id',
        string="Precedentes Similares",
        compute='_compute_available_precedents',
        store=False
    )

    precedent_count = fields.Integer(compute='_compute_available_precedents',string="Cantidad de Precedentes Similares")

    actual_amount_recovered = fields.Monetary(string="Monto Recuperado Real", currency_field='currency_id')
    settlement_amount = fields.Monetary(string="Monto de Acuerdo", currency_field='currency_id')
    actual_duration_days = fields.Integer(string="Duración Real (Días)", compute='_compute_actual_duration', store=True)

    recommended_action = fields.Selection([
        ('accept', 'Aceptar'),
        ('accept_conditional', 'Aceptar con Condiciones'),
        ('negotiate', 'Negociar Terminos'),
        ('decline', 'rechazar'),
    ], string="Accion Recomendada", tracking=True)

    acceptance_conditions = fields.Text(string="Condiciones de Aceptacion", help="Condiciones específicas para aceptar el caso")

    strategy_notes = fields.Text(string="Notas de Estrategia")
    rejection_reasons = fields.Text(string="Razon de Rechazo")

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    lawyer_ids = fields.Many2many(
        'hr.employee',
        'law_case_lawyer_rel',
        'case_id',
        'employee_id',
        string="Equipo de Abogados",
        domain=[('is_lawyer', '=', True)],
        tracking=True,
    )

    opposing_party_ids = fields.Many2many(
        'res.partner',
        'law_case_opposing_party_rel',
        'case_id',
        'partner_id',
        string='Contraparte',
        help='Contraparte del Caso',
        domain=[('is_counterparty', '=', True)]
    )

    practice_area_id = fields.Many2one('law.practice.area', string="Area Legal", tracking=True)

    opposing_party_lawyer_ids = fields.Many2many(
        'res.partner',
        'law_case_opposing_lawyer_rel',
        'case_id',
        'partner_id',
        string='Abogados de la Contraparte',
        help='Abogados que representan a la contraparte'
    )

    milestone_ids = fields.One2many(
        'law.case.milestone',
        'case_id',
        string='Hitos',
    )

    state = fields.Selection([
        # ('intake', 'Intake'),
        #         ('review', 'In Review'),
        #         ('open', 'In Progress'),
        #         ('on_hold', 'On Hold'),
        #         ('settled', 'Settled'),
        #         ('won', 'Won'),
        #         ('lost', 'Lost'),
        #         ('closed', 'Closed'),
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('on_hold', 'En Espera'),
        ('closed', 'Cerrado'),
    ], default='draft', string="Status", tracking=True)

    stage_id = fields.Many2one('law.case.stage', string="Fase", tracking=True)
    open_date = fields.Date(string="Fecha de Apertura")
    close_date = fields.Date(string="Fecha de Cierre")

    short_description = fields.Char(string="Descripción Breve")
    facts = fields.Text(string="Notas del Caso / Hechos")

    # --- decorators and functions ---

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("Values for new case: %s", vals_list)

        # Validate each case before creation
        validation_service = CaseValidationService(self.env)
        empty_case = self.env['law.case'].browse([])

        for vals in vals_list:
            # Run validation
            is_valid, error_msg = validation_service.validate(empty_case, vals)
            if not is_valid:
                raise UserError(error_msg)

            # Generate sequence code
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('law.case') or '/'

        cases = super(LawCase, self).create(vals_list)

        # for case in cases:
        #     case._update_followers()

        return cases

    # --- State Management using State Machine Service ---
    # Old _STATE_TRANSITIONS dictionary replaced with State Pattern

    def _apply_state_transition(self, case, old_state, new_state, local_vals):
        """
        Apply state transition using State Machine Service.
        Replaces old hardcoded dictionary approach with extensible State Pattern.
        """
        state_machine = CaseStateMachine(self.env)

        success, error_msg, modified_vals = state_machine.transition(
            case, old_state, new_state, local_vals
        )

        if not success:
            raise UserError(error_msg)

        # Update local_vals with any modifications made by state hooks
        local_vals.update(modified_vals)

    def get_allowed_state_transitions(self):
        """
        Get allowed state transitions for current case.
        Useful for UI to show available state change buttons.
        """
        self.ensure_one()
        state_machine = CaseStateMachine(self.env)
        return state_machine.get_allowed_transitions(self.state)

    # Old transition methods (_t_open, _t_on_hold, etc.) are now handled by State classes
    # See services/case_state_service.py for implementation


    def write(self, vals):
        _logger.info(F'*****VALUES: {vals}')
        _logger.info(F'*****SELF ENV: {self.env}')

        # Validate before writing
        validation_service = CaseValidationService(self.env)

        for case in self:
            local_vals = dict(vals)

            # Run validation
            is_valid, error_msg = validation_service.validate(case, local_vals)
            if not is_valid:
                raise UserError(error_msg)

            # Handle state transitions
            if 'state' in local_vals:
                old_state = case.state
                new_state = local_vals['state']
                self._apply_state_transition(case, old_state, new_state, local_vals)

            # Handle stage changes that affect state
            if 'stage_id' in local_vals and local_vals['stage_id']:
                new_stage = self.env['law.case.stage'].browse(local_vals['stage_id'])
                if new_stage.is_closed_stage and case.state != 'closed':
                    local_vals['state'] = 'closed'
                    self._apply_state_transition(case, case.state, 'closed', local_vals)

            super(LawCase, case).write(local_vals)

        return True

    # Search override mala practica
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None):
    #     res = super().search(args, offset=offset, limit=limit, order=order)
    #
    #     if self.env.user.has_group('law_firm_management.group_law_manager'):
    #         return res
    #
    #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     _logger.info(f'*****LAWYERS: {employee}')
    #
    #     if employee and employee.is_lawyer:
    #         return res.filtered(lambda c: employee in c.lawyer_ids)
    #
    #     return self.env['law.case']

    @api.depends('open_date', 'close_date')
    def _compute_actual_duration(self):
        for case in self:
            if case.open_date and case.close_date:
                delta = fields.Date.from_string(case.close_date) - fields.Date.from_string(case.open_date)
                case.actual_duration_days = delta.days
            else:
                case.actual_duration_days = 0

    @api.depends('practice_area_id')
    def _compute_available_precedents(self):
        service = PrecedentAnalysisService(self.env)

        for case in self:
            _logger.info(f'===== Computing available precedents for case {case.name} (ID: {case.id}) =====')
            _logger.info(f'Practice Area: {case.practice_area_id.name if case.practice_area_id else "Not Set"}')

            if case.practice_area_id:
                # Use service to find precedents - centralized logic
                precedents = service.find_relevant_precedents(case.practice_area_id.id)
                case.available_precedents = precedents
                case.precedent_count = len(precedents)

                _logger.info(f'Found {len(precedents)} precedents in practice area')
                if precedents:
                    _logger.info(f'Precedent IDs: {precedents.ids}')
                    _logger.info(f'Precedent names: {[p.case_name for p in precedents]}')
            else:
                case.available_precedents = self.env['law.case.precedent'].browse([])
                case.precedent_count = 0
                _logger.info('No practice area set - no precedents available')

            _logger.info(f'===== End computing available precedents for case {case.id} =====\n')

    #TODO: adds a search but idk if _compute_available_precedents is not useful anymore
    @api.depends('practice_area_id', 'client_role')
    def _compute_precedent_analysis(self):
        service = PrecedentAnalysisService(self.env)

        for case in self:
            _logger.info(f'===== Analyzing precedents for case {case.name} (ID: {case.id}) =====')
            _logger.info(f'Client Role: {case.client_role}')
            _logger.info(f'Total available precedents: {case.precedent_count}')

            if not case.client_role or not case.practice_area_id:
                case.has_favorable_precedents = False
                case.favorable_precedents_count = 0
                case.unfavorable_precedents_count = 0
                if not case.client_role:
                    _logger.warning('No client role set - skipping precedent analysis')
                continue

            # Use service to find and analyze precedents - no duplication!
            precedents = service.find_relevant_precedents(case.practice_area_id.id)
            analysis = service.analyze_favorability(precedents, case.client_role)

            case.has_favorable_precedents = bool(analysis['favorable'])
            case.favorable_precedents_count = analysis['favorable_count']
            case.unfavorable_precedents_count = analysis['unfavorable_count']

            _logger.info(
                f"Precedent analysis complete: {analysis['favorable_count']} favorable, "
                f"{analysis['unfavorable_count']} unfavorable "
                f"(ratio: {analysis['favorable_ratio']:.1f}%)"
            )

    # action_calculate_success_rate
    @api.depends('evidence_strength',
                 'case_strength',
                 'client_role',
                 'practice_area_id',
                 'precedent_count',
                 'favorable_precedents_count',
                 'responsible_employee_id',
                 'responsible_employee_id.years_of_experience',
                 )
    def _compute_success_rate(self):
        # Optional: pass config for ML or external service strategies
        # config = {'model_path': '/path/to/model.pkl', 'api_key': 'xxx'}
        service = CaseSuccessRateService(self.env)
        for case in self:
            case.estimated_success_rate = service.compute(case)

    def action_view_client(self):
        self.ensure_one()
        if not self.client_id:
            raise UserError("No hay clientes asignados a este caso.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Cliente',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.client_id.id,
            # 'domain': [('id', '=', self.client_id.id)],
            'target': 'current',
        }