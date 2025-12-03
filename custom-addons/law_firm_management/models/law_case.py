from odoo import models, fields, api
from odoo.exceptions import UserError
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
        'res.partner',
        string="Cliente", required=True, tracking=True,
        domain=[('is_client', '=', True)])

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

    case_strength = fields.Selection([
        ('very_weak', 'Muy Débil'),
        ('weak', 'Débil'),
        ('moderate', 'Moderado'),
        ('strong', 'Fuerte'),
        ('very_string', 'Muy Fuerte'),
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
        ('strong', 'Alto'),
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
    unfavorable_precedents_count = fields.Integer(compute='_compute_precedent_analysis', store=True, string="Numero de precedentes favorables")

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

    @api.model
    def create(self, vals):
        for val in vals:
            if not val.get('code'):
                val['code'] = self.env['ir.sequence'].next_by_code('law.case') or '/'
        case = super().create(vals)
        case._update_followers()
        return case

    def write(self, vals):
        _logger.info(F'*****VALUES: {vals}')
        _logger.info(F'*****SELF ENV: {self.env}')

        if 'state' in vals:
            for case in self:
                old_state = case.state
                new_state = vals['state']

                if new_state == 'open' and not case.responsible_employee_id:
                    raise UserError("Asigna un abogado responsable para abrir el caso")
                if new_state == 'closed':
                    if old_state not in ('open', 'on_hold'):
                        raise UserError("El caso no esta abierto.")
                    else:
                        vals['close_date'] = fields.Date.today()

                if new_state == 'open' and not vals.get('open_date'):
                    vals['open_date'] = fields.Date.today()

                if new_state == 'draft':
                    vals['open_date'] = False
                    vals['close_date'] = False

        if 'stage_id' in vals:
            new_stage = self.env['law.case.stage'].browse(vals['stage_id'])
            if new_stage.is_closed_stage:
                vals['state'] = 'closed'
                vals['close_date'] = fields.Date.today()
        return super().write(vals)

    def _update_followers(self):
        for case in self:
            lawyer_users = case.lawyer_ids.mapped('user_id')
            current_followers = case.message_partner_ids
            lawyers_to_remove = current_followers.filtered(
                lambda p: p.user_ids and
                p.user_ids[0] not in lawyer_users and
                any(emp.is_lawyer for emp in self.env['hr.employee'].search([('user_id', '=', p.user_ids[0].id)]))
            )
            if lawyers_to_remove:
                case.message_unsubscribe(partner_ids=lawyers_to_remove)
                _logger.info(F'*****LAWYERS REMOVED: {lawyers_to_remove}')

            _logger.info(F'*****FOLLOWERS: {current_followers.name}')

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        res = super().search(args, offset=offset, limit=limit, order=order)

        if self.env.user.has_group('law_firm_management.group_law_manager'):
            return res

        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        _logger.info(f'*****LAWYERS: {employee}')

        if employee and employee.is_lawyer:
            return res.filtered(lambda c: employee in c.lawyer_ids)

        return self.env['law.case']

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
        for case in self:
            _logger.info(f'===== Computing available precedents for case {case.name} (ID: {case.id}) =====')
            _logger.info(f'Practice Area: {case.practice_area_id.name if case.practice_area_id else "Not Set"}')

            if case.practice_area_id:
                precedents = self.env['law.case.precedent'].search([
                    ('practice_area_id', '=', case.practice_area_id.id)
                ])
                case.available_precedents = precedents
                case.precedent_count = len(precedents)
                _logger.info(f'Found {len(precedents)} precedents in practice area')
                if precedents:
                    _logger.info(f'Precedent IDs: {precedents.ids}')
                    _logger.info(f'Precedent names: {[p.case_name for p in precedents]}')
            else:
                case.available_precedents = self.env['law.case.precedent']
                case.precedent_count = 0
                _logger.info('No practice area set - no precedents available')

            _logger.info(f'===== End computing available precedents for case {case.id} =====\n')

    @api.depends('precedents_ids', 'precedents_ids.favoured_party', 'client_role')
    def _compute_precedent_analysis(self):
        for case in self:
            _logger.info(f'===== Analyzing precedents for case {case.name} (ID: {case.id}) =====')
            _logger.info(f'Client Role: {case.client_role}')
            _logger.info(f'Total available precedents: {case.precedent_count}')

            if not case.client_role:
                case.has_favorable_precedents = False
                case.favorable_precedents_count = False
                case.unfavorable_precedents_count = False
                _logger.warning('No client role set - skipping precedent analysis')
                continue

            if case.precedent_count > 0:
                favorable = case.available_precedents.filtered(lambda p: p.favoured_party == case.client_role)
                unfavorable = case.available_precedents.filtered(lambda p: p.favoured_party != case.client_role)
                _logger.info(f'Favorable precedents: {len(favorable)} - {[p.case_name for p in favorable]}')
                _logger.info(f'Unfavorable precedents: {len(unfavorable)} - {[p.case_name for p in unfavorable]}')

                case.has_favorable_precedents = len(favorable) > 0
                case.favorable_precedents_count = len(favorable)
                case.unfavorable_precedents_count = len(unfavorable)
            else:
                case.has_favorable_precedents = False
                case.favorable_precedents_count = 0
                case.unfavorable_precedents_count = 0
                _logger.info('No available precedents to analyze')

    # action_calculate_success_rate
    @api.depends('evidence_strength',
                 'case_strength', 'available_precedents',
                 'responsible_employee_id', 'practice_area_id',
                 'responsible_employee_id.years_of_experience',
                 'responsible_employee_id.expert_practice_area_ids',
                 )
    def _compute_success_rate(self):
        for case in self:
            score = 0
            factors = 0

            if case.evidence_strength:
                evidence_scores = {'weak': 10, 'moderate': 40, 'strong': 70,'conclusive': 90}
                score += evidence_scores.get(case.evidence_strength, 0)
                factors += 1

            if case.case_strength:
                strength_score = {'very_weak': 10, 'weak': 30, 'moderate': 50, 'strong': 75, 'very_strong': 95}
                score += strength_score.get(case.case_strength, 0)
                factors += 1

            if case.available_precedents and case.client_role:
                if case.precedent_count > 0:
                    precedent_ratio = (case.favorable_precedents_count / case.precedent_count) * 100

                    score += precedent_ratio
                    factors += 1

            avg_score = (score / factors) if factors > 0 else 0.0

            lawyer_score = 50.0

            if case.responsible_employee_id:
                lawyer = case.responsible_employee_id
                experienced_bonus = min(lawyer.years_of_experience * 2, 20)
                lawyer_score += experienced_bonus

                if case.practice_area_id:
                    domain = [
                        ('responsible_employee_id', '=', lawyer.id),
                        ('practice_area_id', '=', case.practice_area_id.id),
                        ('state', '=', 'closed'),
                        ('case_outcome', 'in', ['won', 'lost']),
                    ]
                    past_cases = self.search(domain)
                    total_past = len(past_cases)

                    if total_past > 0:
                        wins = len(past_cases.filtered(lambda p: p.case_outcome == 'won'))
                        win_rate = (wins / total_past) * 100

                        if win_rate >= 75:
                            lawyer_score += 15
                        elif win_rate >= 50:
                            lawyer_score += 5
                        elif win_rate < 30:
                            lawyer_score -= 10
                        else:
                            lawyer_score -= 5


                active_cases = self.search_count([
                    ('responsible_employee_id', '=', lawyer.id),
                    ('state', '=', 'open'),
                    ('id', '!=', case.id)
                ])
                if active_cases > 5:
                    lawyer_score -= 15

            lawyer_score = max(0, min(100, lawyer_score))

            final_rate = (avg_score * 0.7) + (lawyer_score * 0.3)

            # case.estimated_success_rate = score / factors if factors > 0 else 0
            case.estimated_success_rate = round(final_rate, 2)

    def action_view_client(self):
        self.ensure_one()
        if not self.client_id:
            raise UserError("No hay clientes asignados a este caso.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Clientes',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.client_id.id)],
            'target': 'current',
        }

        if len(self.client_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cliente',
                'res_model': 'res.partner',
                'view_mode': 'form',
                'res_id': self.client_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Clientes',
                'res_model': 'res.partner',
                'view_mode': 'list,form',
                'domain': [('id', 'in', self.client_ids.ids)],
                'target': 'current',
            }