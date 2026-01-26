from odoo import fields
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class CaseEvent:
    """
    Value object representing a case event.
    Immutable event data that observers can react to.
    """

    def __init__(self, event_type, case, old_values=None, new_values=None, context=None):
        """
        Initialize case event.

        :param event_type: String identifier ('created', 'state_changed', 'closed', etc.)
        :param case: law.case record
        :param old_values: Dictionary of old field values
        :param new_values: Dictionary of new field values
        :param context: Optional additional context data
        """
        self.event_type = event_type
        self.case = case
        self.old_values = old_values or {}
        self.new_values = new_values or {}
        self.context = context or {}
        self.timestamp = fields.Datetime.now()

    def get_changed_fields(self):
        """Get list of fields that changed"""
        return list(self.new_values.keys())

    def was_field_changed(self, field_name):
        """Check if a specific field was changed"""
        return field_name in self.new_values

    def get_old_value(self, field_name, default=None):
        """Get old value of a field"""
        return self.old_values.get(field_name, default)

    def get_new_value(self, field_name, default=None):
        """Get new value of a field"""
        return self.new_values.get(field_name, default)

    def __repr__(self):
        return f"CaseEvent(type={self.event_type}, case={self.case.code or self.case.id}, fields={self.get_changed_fields()})"


class CaseEventObserver:
    """
    Abstract base class for case event observers.
    Observers implement the handle() method to react to events.
    """

    def __init__(self, env):
        self.env = env

    def can_handle(self, event):
        """
        Check if this observer should handle the event.
        Override in subclasses to filter events.

        :param event: CaseEvent instance
        :return: Boolean
        """
        return True

    def handle(self, event):
        """
        Handle the event.
        Must be implemented by subclasses.

        :param event: CaseEvent instance
        """
        raise NotImplementedError("Subclasses must implement handle()")

    def get_priority(self):
        """
        Get observer priority (lower number = higher priority).
        Higher priority observers are notified first.

        :return: Integer priority (0-100)
        """
        return 50  # Default medium priority


class CaseEventManager:
    """
    Event manager implementing the Observer pattern.
    Manages observer registration and event notification.
    Singleton pattern for global access.
    """

    _instance = None

    def __init__(self, env):
        self.env = env
        self._observers = []  # List of (priority, observer) tuples
        self._event_log = []  # Optional: Keep log of recent events
        self._max_log_size = 100

    @classmethod
    def get_instance(cls, env):
        """
        Get or create singleton instance.

        :param env: Odoo environment
        :return: CaseEventManager instance
        """
        # Note: In Odoo, we create instance per request, not true singleton
        # But we can use environment context to cache if needed
        return cls(env)

    def register_observer(self, observer):
        """
        Register an observer.

        :param observer: CaseEventObserver instance
        """
        if not isinstance(observer, CaseEventObserver):
            raise ValueError("Observer must be instance of CaseEventObserver")

        priority = observer.get_priority()
        self._observers.append((priority, observer))

        # Sort by priority (lower number = higher priority)
        self._observers.sort(key=lambda x: x[0])

        _logger.info(f"Registered observer: {observer.__class__.__name__} (priority={priority})")

    def unregister_observer(self, observer_class):
        """
        Unregister all observers of a specific class.

        :param observer_class: Class of observer to remove
        """
        original_count = len(self._observers)
        self._observers = [
            (priority, obs) for priority, obs in self._observers
            if not isinstance(obs, observer_class)
        ]
        removed = original_count - len(self._observers)
        _logger.info(f"Unregistered {removed} observer(s) of type {observer_class.__name__}")

    def notify(self, event):
        """
        Notify all observers of an event.
        Observers are notified in priority order.

        :param event: CaseEvent instance
        """
        if not isinstance(event, CaseEvent):
            raise ValueError("Event must be instance of CaseEvent")

        _logger.info(f"Notifying observers of event: {event}")

        # Log event
        self._log_event(event)

        # Notify observers in priority order
        for priority, observer in self._observers:
            try:
                if observer.can_handle(event):
                    _logger.debug(
                        f"Observer {observer.__class__.__name__} handling event {event.event_type}"
                    )
                    observer.handle(event)
            except Exception as e:
                # Don't let one observer failure break the chain
                _logger.error(
                    f"Error in observer {observer.__class__.__name__}: {e}",
                    exc_info=True
                )

    def notify_async(self, event):
        """
        Notify observers asynchronously (using Odoo queue if available).
        Falls back to synchronous if no queue system.

        :param event: CaseEvent instance
        """
        # TODO: Implement async notification using Odoo queue_job if available
        # For now, fall back to synchronous
        self.notify(event)

    def _log_event(self, event):
        """Log event for debugging/audit purposes"""
        self._event_log.append(event)

        # Keep log size manageable
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

    def get_recent_events(self, limit=10):
        """Get recent events for debugging"""
        return self._event_log[-limit:]

    def clear_observers(self):
        """Clear all registered observers (useful for testing)"""
        self._observers = []
        _logger.info("Cleared all observers")


# Convenience functions for creating common events

def create_case_created_event(case):
    """Create event for case creation"""
    return CaseEvent('case_created', case)


def create_state_changed_event(case, old_state, new_state):
    """Create event for state change"""
    return CaseEvent(
        'state_changed',
        case,
        old_values={'state': old_state},
        new_values={'state': new_state}
    )


def create_case_closed_event(case, outcome=None):
    """Create event for case closure"""
    return CaseEvent(
        'case_closed',
        case,
        context={'outcome': outcome or case.case_outcome}
    )


def create_case_overdue_event(case):
    """Create event for case becoming overdue"""
    return CaseEvent('case_overdue', case)


def create_case_approaching_deadline_event(case, days_remaining):
    """Create event for case approaching deadline"""
    return CaseEvent(
        'case_approaching_deadline',
        case,
        context={'days_remaining': days_remaining}
    )


def create_lawyer_assigned_event(case, old_lawyer_id, new_lawyer_id):
    """Create event for lawyer assignment change"""
    return CaseEvent(
        'lawyer_assigned',
        case,
        old_values={'responsible_employee_id': old_lawyer_id},
        new_values={'responsible_employee_id': new_lawyer_id}
    )


def create_case_updated_event(case, old_values, new_values):
    """Create generic update event"""
    return CaseEvent('case_updated', case, old_values, new_values)
