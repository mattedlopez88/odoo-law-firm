"""
Case State Machine Service
Implements State Pattern for case state transitions
Replaces hardcoded _STATE_TRANSITIONS dictionary with extensible state objects
"""
from odoo import fields, _
import logging

_logger = logging.getLogger(__name__)


class CaseState:
    """
    Base state interface - Open/Closed Principle.
    Each state defines its own allowed transitions and behavior.
    """

    def __init__(self, env):
        self.env = env

    def get_state_name(self):
        """Return the state identifier"""
        raise NotImplementedError("Subclasses must implement get_state_name()")

    def allowed_transitions(self):
        """
        Return list of allowed target states.
        Override in subclasses to define state-specific transitions.
        """
        return []

    def can_transition_to(self, target_state):
        """Check if transition to target state is allowed"""
        return target_state in self.allowed_transitions()

    def on_enter(self, case, vals):
        """
        Hook called when entering this state.
        Can modify vals dictionary to set required fields.

        :param case: law.case record
        :param vals: Dictionary of values being written
        :return: Tuple (success: bool, error_message: str or None)
        """
        _logger.debug(f"Entering state {self.get_state_name()} for case {case.code or case.id}")
        return True, None

    def on_exit(self, case, vals):
        """
        Hook called when leaving this state.
        Can validate requirements before leaving.

        :param case: law.case record
        :param vals: Dictionary of values being written
        :return: Tuple (success: bool, error_message: str or None)
        """
        _logger.debug(f"Exiting state {self.get_state_name()} for case {case.code or case.id}")
        return True, None

    def validate(self, case, vals):
        """
        Validate state-specific requirements.

        :param case: law.case record
        :param vals: Dictionary of values
        :return: Tuple (success: bool, error_message: str or None)
        """
        return True, None

    def get_required_fields(self):
        """
        Return list of field names required in this state.
        Can be used for UI validation or mandatory field checks.
        """
        return []


class DraftState(CaseState):
    """
    Draft state - Initial state for new cases.
    Cases can be edited freely without restrictions.
    """

    def get_state_name(self):
        return 'draft'

    def allowed_transitions(self):
        return ['open']

    #TODO: Use validation service?
    def on_exit(self, case, vals):
        """Validate requirements before opening case"""
        # Check if responsible lawyer is assigned
        responsible = vals.get('responsible_employee_id',
                              case.responsible_employee_id.id if case.responsible_employee_id else None)

        if not responsible:
            return False, _("Debe asignar un abogado responsable antes de abrir el caso.")

        return True, None

    def get_required_fields(self):
        return ['name', 'client_id']


class OpenState(CaseState):
    """
    Open state - Case is actively being worked on.
    Requires responsible lawyer and tracks open date.
    """

    def get_state_name(self):
        return 'open'

    def allowed_transitions(self):
        return ['on_hold', 'closed']

    def on_enter(self, case, vals):
        """Set open date when case is opened"""
        # Set open_date if not already set
        if not case.open_date and not vals.get('open_date'):
            vals['open_date'] = fields.Date.today()
            _logger.info(f"Setting open_date to {vals['open_date']} for case {case.code or case.id}")

        # Clear close_date when reopening
        if vals.get('state') == 'open':
            vals.setdefault('close_date', False)

        return True, None

    def validate(self, case, vals):
        """Validate open case requirements"""
        responsible = vals.get('responsible_employee_id',
                              case.responsible_employee_id.id if case.responsible_employee_id else None)

        if not responsible:
            return False, _("Un caso abierto debe tener un abogado responsable asignado.")

        return True, None

    def get_required_fields(self):
        return ['name', 'client_id', 'responsible_employee_id', 'practice_area_id']


class OnHoldState(CaseState):
    """
    On Hold state - Case is temporarily paused.
    Can be resumed or closed.
    """

    def get_state_name(self):
        return 'on_hold'

    def allowed_transitions(self):
        return ['open', 'closed']

    def on_enter(self, case, vals):
        """Optional: Log reason for putting case on hold"""
        _logger.info(f"Case {case.code or case.id} put on hold")
        return True, None

    def on_exit(self, case, vals):
        """Optional: Validate when resuming from hold"""
        return True, None


class ClosedState(CaseState):
    """
    Closed state - Case is completed.
    Sets close date and can optionally require outcome.
    """

    def get_state_name(self):
        return 'closed'

    def allowed_transitions(self):
        # Can reopen case if needed (with restrictions)
        return ['draft']

    def on_enter(self, case, vals):
        """Set close date and calculate duration when closing case"""
        # Set close_date if not already set
        if not vals.get('close_date'):
            vals['close_date'] = fields.Date.today()
            _logger.info(f"Setting close_date to {vals['close_date']} for case {case.code or case.id}")

        # Calculate actual duration if open_date exists
        if case.open_date and vals.get('close_date'):
            from datetime import date
            if isinstance(vals['close_date'], str):
                close_date = fields.Date.from_string(vals['close_date'])
            else:
                close_date = vals['close_date']

            open_date = fields.Date.from_string(case.open_date) if isinstance(case.open_date, str) else case.open_date

            delta = close_date - open_date
            vals['actual_duration_days'] = delta.days
            _logger.info(f"Calculated duration: {delta.days} days")

        return True, None

    def on_exit(self, case, vals):
        """Validate before reopening a closed case"""
        # Optional: Add permission check or validation
        _logger.warning(f"Reopening closed case {case.code or case.id}")
        return True, None

    def validate(self, case, vals):
        """Optional: Validate that outcome is set when closing"""
        outcome = vals.get('case_outcome', case.case_outcome if case else None)

        if not outcome:
            _logger.warning(
                f"Closing case {case.code or case.id} without setting outcome. "
                "Consider setting case_outcome field."
            )
            # Don't block - just warn

        return True, None

    def get_required_fields(self):
        return ['name', 'client_id', 'responsible_employee_id', 'close_date']


class CaseStateMachine:
    """
    State machine orchestrator.
    Manages state objects and coordinates transitions.
    """

    # Registry of available states
    STATES = {
        'draft': DraftState,
        'open': OpenState,
        'on_hold': OnHoldState,
        'closed': ClosedState,
    }

    def __init__(self, env):
        self.env = env
        # Instantiate all state objects
        self._states = {
            state_key: state_class(env)
            for state_key, state_class in self.STATES.items()
        }

    def get_state(self, state_name):
        """Get state object by name"""
        return self._states.get(state_name)

    def transition(self, case, old_state, new_state, vals):
        """
        Execute state transition with validation and hooks.

        :param case: law.case record
        :param old_state: Current state name
        :param new_state: Target state name
        :param vals: Dictionary of values being written
        :return: Tuple (success: bool, error_message: str or None, modified_vals: dict)
        """
        _logger.info(
            f"Attempting state transition for case {case.code or case.id}: "
            f"{old_state} → {new_state}"
        )

        # No transition needed
        if old_state == new_state:
            return True, None, vals

        # Get state objects
        current_state_obj = self._states.get(old_state)
        target_state_obj = self._states.get(new_state)

        if not current_state_obj:
            error_msg = _("Estado actual inválido: %s") % old_state
            _logger.error(error_msg)
            return False, error_msg, vals

        if not target_state_obj:
            error_msg = _("Estado destino inválido: %s") % new_state
            _logger.error(error_msg)
            return False, error_msg, vals

        # Check if transition is allowed
        if not current_state_obj.can_transition_to(new_state):
            error_msg = _("Transición de estado no permitida: %s → %s") % (old_state, new_state)
            _logger.warning(error_msg)
            return False, error_msg, vals

        # Execute on_exit hook for current state
        success, error_msg = current_state_obj.on_exit(case, vals)
        if not success:
            _logger.warning(f"on_exit failed for {old_state}: {error_msg}")
            return False, error_msg, vals

        # Execute on_enter hook for target state
        success, error_msg = target_state_obj.on_enter(case, vals)
        if not success:
            _logger.warning(f"on_enter failed for {new_state}: {error_msg}")
            return False, error_msg, vals

        # Validate target state requirements
        success, error_msg = target_state_obj.validate(case, vals)
        if not success:
            _logger.warning(f"Validation failed for {new_state}: {error_msg}")
            return False, error_msg, vals

        _logger.info(f"State transition successful: {old_state} → {new_state}")
        return True, None, vals

    def get_allowed_transitions(self, current_state):
        """
        Get list of allowed transitions from current state.
        Useful for UI to show available actions.

        :param current_state: Current state name
        :return: List of allowed target state names
        """
        state_obj = self._states.get(current_state)
        if not state_obj:
            return []
        return state_obj.allowed_transitions()

    def get_required_fields(self, state_name):
        """
        Get required fields for a state.
        Useful for form validation.

        :param state_name: State name
        :return: List of required field names
        """
        state_obj = self._states.get(state_name)
        if not state_obj:
            return []
        return state_obj.get_required_fields()

    @classmethod
    def register_state(cls, state_key, state_class):
        """
        Dynamically register a new state.
        Useful for custom modules or extensions.

        :param state_key: State identifier (e.g., 'in_litigation')
        :param state_class: State class (must inherit from CaseState)
        """
        if not issubclass(state_class, CaseState):
            raise ValueError(f"{state_class} must inherit from CaseState")

        cls.STATES[state_key] = state_class
        _logger.info(f"Registered new state: {state_key}")
