from ..case_event_manager import CaseEventObserver
import logging

_logger = logging.getLogger(__name__)


class DeadlineObserver(CaseEventObserver):
    """
    Observer that monitors case deadlines and creates calendar activities.
    Single Responsibility: Deadline monitoring only.
    """

    def get_priority(self):
        """Medium-low priority"""
        return 60

    def can_handle(self, event):
        """Handle events that affect deadlines"""
        return event.event_type in [
            'case_created',
            'state_changed',
            'case_updated',
            'case_overdue',
            'case_approaching_deadline'
        ]

    def handle(self, event):
        """
        Monitor deadlines and create activities/reminders.

        :param event: CaseEvent instance
        """
        case = event.case

        if event.event_type == 'case_created':
            self._schedule_deadline_reminder(case)

        elif event.event_type == 'state_changed':
            new_state = event.get_new_value('state')
            if new_state == 'open':
                self._schedule_deadline_reminder(case)
            elif new_state == 'closed':
                self._cancel_deadline_reminders(case)

        elif event.event_type == 'case_updated':
            # Check if deadline-related fields changed
            if 'estimated_duration_months' in event.get_changed_fields():
                self._reschedule_deadline_reminder(case)

        elif event.event_type == 'case_overdue':
            self._create_overdue_activity(case)

        elif event.event_type == 'case_approaching_deadline':
            self._create_deadline_warning_activity(case, event)

    def _schedule_deadline_reminder(self, case):
        """
        Schedule a reminder activity for case deadline.

        :param case: law.case record
        """
        if not case.open_date or case.state != 'open':
            return

        if not case.estimated_duration_months or case.estimated_duration_months <= 0:
            return

        # Calculate expected close date
        from datetime import timedelta
        expected_close_date = case.open_date + timedelta(days=case.estimated_duration_months * 30)

        # Schedule reminder 7 days before deadline
        reminder_date = expected_close_date - timedelta(days=7)

        try:
            # Create calendar activity
            self.env['mail.activity'].create({
                'res_id': case.id,
                'res_model_id': self.env['ir.model']._get_id('law.case'),
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': reminder_date,
                'summary': f'Caso próximo a vencer: {case.name}',
                'note': f'Este caso vence el {expected_close_date.strftime("%Y-%m-%d")}. Por favor revisar el progreso.',
                'user_id': case.responsible_employee_id.user_id.id if case.responsible_employee_id and case.responsible_employee_id.user_id else self.env.user.id,
            })

            _logger.info(f"Scheduled deadline reminder for case {case.code} on {reminder_date}")

        except Exception as e:
            _logger.error(f"Failed to schedule deadline reminder for case {case.code}: {e}")

    def _cancel_deadline_reminders(self, case):
        """
        Cancel pending deadline reminder activities.

        :param case: law.case record
        """
        try:
            activities = self.env['mail.activity'].search([
                ('res_id', '=', case.id),
                ('res_model_id', '=', self.env['ir.model']._get_id('law.case')),
                ('summary', 'ilike', 'próximo a vencer')
            ])

            if activities:
                activities.unlink()
                _logger.info(f"Cancelled {len(activities)} deadline reminder(s) for case {case.code}")

        except Exception as e:
            _logger.error(f"Failed to cancel deadline reminders for case {case.code}: {e}")

    def _reschedule_deadline_reminder(self, case):
        """
        Reschedule deadline reminder when duration estimate changes.

        :param case: law.case record
        """
        self._cancel_deadline_reminders(case)
        self._schedule_deadline_reminder(case)

    def _create_overdue_activity(self, case):
        """
        Create urgent activity for overdue case.

        :param case: law.case record
        """
        from datetime import date

        try:
            self.env['mail.activity'].create({
                'res_id': case.id,
                'res_model_id': self.env['ir.model']._get_id('law.case'),
                'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                'date_deadline': date.today(),
                'summary': f'⚠️ Caso ATRASADO: {case.name}',
                'note': f'Este caso está atrasado por {case.days_overdue} días. Se requiere atención inmediata.',
                'user_id': case.responsible_employee_id.user_id.id if case.responsible_employee_id and case.responsible_employee_id.user_id else self.env.user.id,
            })

            _logger.warning(f"Created overdue activity for case {case.code}")

        except Exception as e:
            _logger.error(f"Failed to create overdue activity for case {case.code}: {e}")

    def _create_deadline_warning_activity(self, case, event):
        """
        Create activity warning about approaching deadline.

        :param case: law.case record
        :param event: CaseEvent with days_remaining context
        """
        from datetime import date
        days_remaining = event.context.get('days_remaining', case.days_remaining)

        try:
            self.env['mail.activity'].create({
                'res_id': case.id,
                'res_model_id': self.env['ir.model']._get_id('law.case'),
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': date.today(),
                'summary': f'⏰ Caso próximo a vencer: {case.name}',
                'note': f'Este caso vence en {days_remaining} días. Por favor revisar y actualizar.',
                'user_id': case.responsible_employee_id.user_id.id if case.responsible_employee_id and case.responsible_employee_id.user_id else self.env.user.id,
            })

            _logger.info(f"Created deadline warning activity for case {case.code}")

        except Exception as e:
            _logger.error(f"Failed to create deadline warning activity for case {case.code}: {e}")
