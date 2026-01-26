"""
Notification Observer - Sends notifications when important case events occur
"""
from ..case_event_manager import CaseEventObserver
from ...repositories.lawyer_repository import LawyerRepository
import logging

_logger = logging.getLogger(__name__)


class NotificationObserver(CaseEventObserver):
    """
    Observer that sends notifications (chatter messages, emails, etc.)
    when important events occur.
    Single Responsibility: Notification logic only.
    """

    def __init__(self, env):
        super().__init__(env)
        self.lawyer_repo = LawyerRepository(env)

    def get_priority(self):
        """Medium priority - notifications after critical updates"""
        return 40

    def can_handle(self, event):
        """Handle various notification-worthy events"""
        return event.event_type in [
            'case_created',
            'state_changed',
            'case_closed',
            'case_overdue',
            'case_approaching_deadline',
            'lawyer_assigned'
        ]

    def handle(self, event):
        """
        Send appropriate notifications based on event type.

        :param event: CaseEvent instance
        """
        handlers = {
            'case_created': self._notify_case_created,
            'state_changed': self._notify_state_changed,
            'case_closed': self._notify_case_closed,
            'case_overdue': self._notify_case_overdue,
            'case_approaching_deadline': self._notify_approaching_deadline,
            'lawyer_assigned': self._notify_lawyer_assigned,
        }

        handler = handlers.get(event.event_type)
        if handler:
            try:
                handler(event.case, event)
            except Exception as e:
                _logger.error(
                    f"Error sending notification for {event.event_type}: {e}",
                    exc_info=True
                )

    def _notify_case_created(self, case, event):
        case.message_post(
            body=f"Caso creado: {case.name}",
            subject="Nuevo Caso",
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )
        _logger.info(f"Sent case created notification for {case.code}")

    def _notify_state_changed(self, case, event):
        old_state = event.get_old_value('state')
        new_state = event.get_new_value('state')

        state_labels = {
            'draft': 'Borrador',
            'open': 'Abierto',
            'on_hold': 'En Espera',
            'closed': 'Cerrado'
        }

        old_label = state_labels.get(old_state, old_state)
        new_label = state_labels.get(new_state, new_state)

        case.message_post(
            body=f"Estado del caso cambió de <b>{old_label}</b> a <b>{new_label}</b>",
            subject="Cambio de Estado",
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )
        _logger.info(f"Sent state change notification for {case.code}: {old_state} → {new_state}")

    def _notify_case_closed(self, case, event):
        """Notify when case is closed"""
        outcome = event.context.get('outcome') or case.case_outcome

        outcome_labels = {
            'won': '✅ Ganado',
            'lost': '❌ Perdido',
            'settled': '🤝 Acuerdo',
            'dismissed': '📋 Desestimado',
            'withdrawn': '↩️ Retirado',
        }

        outcome_label = outcome_labels.get(outcome, outcome or 'Sin especificar')

        message_body = f"""
        <div style="padding: 10px; border-left: 4px solid #4CAF50;">
            <h3>Caso Cerrado</h3>
            <p><strong>Resultado:</strong> {outcome_label}</p>
            <p><strong>Duración:</strong> {case.actual_duration_days or 0} días</p>
        </div>
        """

        case.message_post(
            body=message_body,
            subject="Caso Cerrado",
            message_type='notification',
            subtype_xmlid='mail.mt_comment'  # Use comment to make it more visible
        )

        _logger.info(f"Sent case closed notification for {case.code} (outcome: {outcome})")

    def _notify_case_overdue(self, case, event):
        """Notify when case becomes overdue"""
        days_overdue = case.days_overdue

        message_body = f"""
        <div style="padding: 10px; border-left: 4px solid #F44336;">
            <h3>⚠️ Caso Atrasado</h3>
            <p>Este caso ha excedido su duración estimada por <strong>{days_overdue} días</strong>.</p>
            <p>Se recomienda revisar el progreso y actualizar la estimación si es necesario.</p>
        </div>
        """

        case.message_post(
            body=message_body,
            subject="⚠️ Caso Atrasado",
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
            partner_ids=case.lawyer_ids.mapped('user_id.partner_id').ids
        )

        _logger.warning(f"Sent overdue notification for case {case.code} ({days_overdue} days)")

    def _notify_approaching_deadline(self, case, event):
        """Notify when case is approaching deadline"""
        days_remaining = event.context.get('days_remaining', case.days_remaining)

        message_body = f"""
        <div style="padding: 10px; border-left: 4px solid #FF9800;">
            <h3>⏰ Caso Próximo a Vencer</h3>
            <p>Este caso vence en <strong>{days_remaining} días</strong>.</p>
            <p>Fecha estimada de cierre: {case.open_date}</p>
        </div>
        """

        case.message_post(
            body=message_body,
            subject="⏰ Caso Próximo a Vencer",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
            partner_ids=case.lawyer_ids.mapped('user_id.partner_id').ids
        )

        _logger.info(f"Sent deadline warning for case {case.code} ({days_remaining} days remaining)")

    def _notify_lawyer_assigned(self, case, event):
        """
        Notify when responsible lawyer is assigned or changed.
        Uses LawyerRepository instead of direct ORM.
        """
        old_lawyer_id = event.get_old_value('responsible_employee_id')
        new_lawyer_id = event.get_new_value('responsible_employee_id')

        if not new_lawyer_id:
            return

        new_lawyer = self.lawyer_repo.find_by_id(new_lawyer_id)

        if old_lawyer_id:
            old_lawyer = self.lawyer_repo.find_by_id(old_lawyer_id)
            message = f"Abogado responsable cambió de <b>{old_lawyer.name}</b> a <b>{new_lawyer.name}</b>"
        else:
            message = f"<b>{new_lawyer.name}</b> asignado como abogado responsable"

        case.message_post(
            body=message,
            subject="Asignación de Abogado",
            message_type='notification',
            subtype_xmlid='mail.mt_note',
            partner_ids=[new_lawyer.user_id.partner_id.id] if new_lawyer.user_id else []
        )

        _logger.info(f"Sent lawyer assignment notification for case {case.code}")
