"""
Case Validation Service
Implements Chain of Responsibility + Specification Pattern
Provides reusable, testable validators for case data
"""
from odoo import _
import logging

_logger = logging.getLogger(__name__)


class CaseValidator:
    """
    Base validator interface - Single Responsibility Principle.
    Each validator checks ONE specific business rule.
    """
    def __init__(self, env):
        self.env = env

    def validate(self, case, vals):
        """
        Validate case data.

        :param case: law.case record (can be empty for create operations)
        :param vals: Dictionary of values being created/written
        :return: True if valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def get_error_message(self):
        """
        Return error message if validation fails.

        :return: String error message
        """
        raise NotImplementedError("Subclasses must implement get_error_message()")

class ResponsibleLawyerValidator(CaseValidator):
    def validate(self, case, vals):
        state = vals.get('state', case.state if case else 'draft')
        responsible = vals.get('responsible_employee_id',
                              case.responsible_employee_id.id if case and case.responsible_employee_id else None)

        # Only required when state is 'open'
        if state == 'open' and not responsible:
            return False
        return True

    def get_error_message(self):
        return _("Asigna un abogado responsable para abrir el caso.")


class ClientRoleValidator(CaseValidator):
    """Validates that client role is set for precedent analysis."""

    def validate(self, case, vals):
        client_role = vals.get('client_role', case.client_role if case else None)
        state = vals.get('state', case.state if case else 'draft')

        # Client role should be set before opening case for proper precedent analysis
        if state == 'open' and not client_role:
            _logger.warning("Opening case without client role - precedent analysis will be limited")
            # Not blocking, just a warning

        return True

    def get_error_message(self):
        return _("Se recomienda especificar el rol del cliente para análisis de precedentes.")


class FinancialDataValidator(CaseValidator):
    """Validates financial data consistency."""

    def validate(self, case, vals):
        claim = vals.get('estimated_amount_claim',
                        case.estimated_amount_claim if case else 0) or 0
        recovery = vals.get('estimated_amount_recovery',
                           case.estimated_amount_recovery if case else 0) or 0
        costs = vals.get('estimated_legal_costs',
                        case.estimated_legal_costs if case else 0) or 0

        # Recovery cannot exceed claim
        if recovery > claim and claim > 0:
            return False

        # Costs cannot be negative
        if costs < 0:
            return False

        # Claim cannot be negative
        if claim < 0:
            return False

        return True

    def get_error_message(self):
        return _("Datos financieros inválidos: la recuperación estimada no puede exceder el monto reclamado, y los montos no pueden ser negativos.")


class PracticeAreaValidator(CaseValidator):
    """Validates that practice area is set before opening case."""

    def validate(self, case, vals):
        practice_area = vals.get('practice_area_id',
                                 case.practice_area_id.id if case and case.practice_area_id else None)
        state = vals.get('state', case.state if case else 'draft')

        # Practice area recommended for open cases
        if state == 'open' and not practice_area:
            _logger.warning("Opening case without practice area")

        return True

    def get_error_message(self):
        return _("Se recomienda especificar el área de práctica.")


class CounterpartyRoleValidator(CaseValidator):
    """Validates counterparty role consistency with client role."""

    def validate(self, case, vals):
        client_role = vals.get('client_role', case.client_role if case else None)

        # Counterparty role is computed, so this is mostly for data consistency
        if client_role and client_role not in ('plaintiff', 'defendant'):
            return False

        return True

    def get_error_message(self):
        return _("Rol del cliente inválido. Debe ser 'Demandante' o 'Demandado'.")


class StateTransitionValidator(CaseValidator):
    """Validates that state transitions are valid."""

    VALID_TRANSITIONS = {
        'draft': ['open'],
        'open': ['on_hold', 'closed'],
        'on_hold': ['open', 'closed'],
        'closed': ['draft'],  # Can reopen with restrictions
    }

    def __init__(self, env):
        super().__init__(env)
        self.old_state = None
        self.new_state = None

    def validate(self, case, vals):
        if 'state' not in vals:
            return True

        self.old_state = case.state if case else 'draft'
        self.new_state = vals['state']

        if self.old_state == self.new_state:
            return True

        allowed_transitions = self.VALID_TRANSITIONS.get(self.old_state, [])
        return self.new_state in allowed_transitions

    def get_error_message(self):
        return _("Transición de estado no válida: %s → %s") % (self.old_state, self.new_state)


class ClosedCaseValidator(CaseValidator):
    """Validates that closed cases have required outcome information."""

    def validate(self, case, vals):
        state = vals.get('state', case.state if case else 'draft')

        if state == 'closed':
            # Outcome should be set when closing
            outcome = vals.get('case_outcome', case.case_outcome if case else None)
            if not outcome:
                _logger.warning("Closing case without setting outcome")
                # Not blocking - can be set later

        return True

    def get_error_message(self):
        return _("Se recomienda especificar el resultado al cerrar el caso.")


class CaseValidationService:
    """
    Orchestrates validation using Chain of Responsibility pattern.
    Open/Closed Principle: Easy to add new validators without modifying this class.
    """

    def __init__(self, env):
        self.env = env
        # Register all validators - easy to add/remove
        self.validators = [
            StateTransitionValidator(env),
            ResponsibleLawyerValidator(env),
            FinancialDataValidator(env),
            CounterpartyRoleValidator(env),
            # Non-blocking validators (warnings only)
            ClientRoleValidator(env),
            PracticeAreaValidator(env),
            ClosedCaseValidator(env),
        ]

    def validate(self, case, vals):
        """
        Validates case data before create/write operations.

        :param case: law.case record (can be empty recordset for create)
        :param vals: Dictionary of values to validate
        :return: Tuple (is_valid: bool, error_message: str or None)
        """
        for validator in self.validators:
            try:
                if not validator.validate(case, vals):
                    error_msg = validator.get_error_message()
                    _logger.warning(
                        f"Validation failed: {validator.__class__.__name__} - {error_msg}"
                    )
                    return False, error_msg
            except Exception as e:
                _logger.error(
                    f"Error in validator {validator.__class__.__name__}: {e}",
                    exc_info=True
                )
                # Continue with other validators
                continue

        return True, None

    def add_validator(self, validator):
        """
        Dynamically add a validator at runtime.
        Useful for plugins or custom extensions.

        :param validator: Instance of CaseValidator subclass
        """
        if not isinstance(validator, CaseValidator):
            raise ValueError("Validator must be an instance of CaseValidator")
        self.validators.append(validator)

    def remove_validator(self, validator_class):
        """
        Remove a validator by class.

        :param validator_class: Class of validator to remove
        """
        self.validators = [
            v for v in self.validators
            if not isinstance(v, validator_class)
        ]
