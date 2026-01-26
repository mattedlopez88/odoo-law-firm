from ..case_event_manager import CaseEventObserver
import logging

_logger = logging.getLogger(__name__)


class AuditLogObserver(CaseEventObserver):
    """
    Observer that creates audit log entries for all case changes.
    Single Responsibility: Audit logging only.

    Note: This is a simple implementation. For production, you might want
    to use a dedicated audit.log model.
    """

    def get_priority(self):
        """Low priority - audit after other critical operations"""
        return 80

    def can_handle(self, event):
        """Log all events"""
        return True

    def handle(self, event):
        """
        Create audit log entry.

        :param event: CaseEvent instance
        """
        case = event.case

        # Build audit message
        audit_message = self._build_audit_message(event)

        # Log to Python logger (always)
        _logger.info(f"AUDIT: Case {case.code} - {audit_message}")

        # Optionally: Create database audit record
        # This would require creating a law.case.audit.log model
        # For now, we'll use chatter with a special note subtype
        if self._should_log_to_chatter(event):
            self._log_to_chatter(case, audit_message, event)

    def _build_audit_message(self, event):
        """Build human-readable audit message"""
        messages = {
            'case_created': 'Caso creado',
            'state_changed': self._format_state_change(event),
            'case_closed': 'Caso cerrado',
            'case_updated': self._format_field_changes(event),
            'lawyer_assigned': self._format_lawyer_assignment(event),
            'case_overdue': 'Caso marcado como atrasado',
            'case_approaching_deadline': 'Caso próximo a vencer',
        }

        return messages.get(
            event.event_type,
            f"Evento: {event.event_type}"
        )

    def _format_state_change(self, event):
        """Format state change message"""
        old_state = event.get_old_value('state')
        new_state = event.get_new_value('state')
        return f"Estado cambió: {old_state} → {new_state}"

    def _format_field_changes(self, event):
        """Format field changes message"""
        changed_fields = event.get_changed_fields()
        if not changed_fields:
            return "Caso actualizado"

        # List changed fields
        field_list = ', '.join(changed_fields)
        return f"Campos actualizados: {field_list}"

    def _format_lawyer_assignment(self, event):
        """Format lawyer assignment message"""
        old_id = event.get_old_value('responsible_employee_id')
        new_id = event.get_new_value('responsible_employee_id')

        if old_id and new_id:
            return f"Abogado responsable cambió (ID: {old_id} → {new_id})"
        elif new_id:
            return f"Abogado responsable asignado (ID: {new_id})"
        else:
            return "Abogado responsable removido"

    def _should_log_to_chatter(self, event):
        """
        Determine if event should be logged to chatter.
        Only log important events to avoid cluttering chatter.
        """
        important_events = [
            'case_created',
            'state_changed',
            'case_closed',
            'lawyer_assigned'
        ]
        return event.event_type in important_events

    def _log_to_chatter(self, case, message, event):
        """Log audit message to case chatter"""
        # Use tracking value if available
        tracking_message = f"📋 <small><i>{message}</i></small>"

        # Don't create notification, just log
        try:
            case.message_post(
                body=tracking_message,
                message_type='notification',
                subtype_xmlid='mail.mt_note',
                author_id=self.env.user.partner_id.id,
            )
        except Exception as e:
            _logger.error(f"Failed to log to chatter: {e}")


class AuditLogModelObserver(CaseEventObserver):
    """
    Alternative observer that logs to a dedicated audit log model.
    Commented out for now - implement if you create law.case.audit.log model.
    """

    def get_priority(self):
        return 90

    def can_handle(self, event):
        return True

    def handle(self, event):
        """
        Create audit log record in database.

        Requires creating a model like:

        class LawCaseAuditLog(models.Model):
            _name = 'law.case.audit.log'

            case_id = fields.Many2one('law.case', required=True)
            event_type = fields.Char()
            event_data = fields.Json()
            user_id = fields.Many2one('res.users')
            timestamp = fields.Datetime()
        """
        # TODO: Implement when audit log model is created
        pass
