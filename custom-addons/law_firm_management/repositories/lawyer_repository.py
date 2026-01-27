from .base_repos import BaseRepository
import logging

_logger = logging.getLogger(__name__)


class LawyerRepository(BaseRepository):

    def _get_model_name(self):
        return 'hr.employee'

    # --- Basic Lawyer Queries ---

    def find_all_lawyers(self, order='name asc'):
        return self.find_all([('is_lawyer', '=', True)], order=order)

    def find_lawyer_by_id(self, lawyer_id):
        lawyer = self.find_by_id(lawyer_id)
        if lawyer and lawyer.is_lawyer:
            return lawyer
        return self.model.browse([])

    def find_lawyer_by_user_id(self, user_id):
        return self.find_one([
            ('user_id', '=', user_id),
            ('is_lawyer', '=', True)
        ])

    # --- Availability & Workload ---

    def find_available_lawyers(self, practice_area_id=None):
        """
        Find lawyers who are available (not overloaded).

        :param practice_area_id: Optional filter by practice area expertise
        :return: Recordset of available lawyers
        """
        domain = [('is_lawyer', '=', True)]

        if practice_area_id:
            domain.append(('expert_practice_area_ids', 'in', [practice_area_id]))

        # TODO: Add workload filtering when case count is available
        # For now, return all lawyers matching domain
        return self.find_all(domain)

    def find_overloaded_lawyers(self, max_active_cases=5):
        """
        Find lawyers with too many active cases.

        :param max_active_cases: Maximum acceptable active cases
        :return: Recordset of overloaded lawyers
        """
        all_lawyers = self.find_all_lawyers()

        # Filter by case count (requires computing case count)
        overloaded = all_lawyers.filtered(
            lambda l: l.case_count > max_active_cases
        )

        return overloaded

    # --- Expertise & Specialization ---

    def find_lawyers_by_practice_area(self, practice_area_id):
        """
        Find lawyers specialized in a practice area.

        :param practice_area_id: Practice area ID
        :return: Recordset of specialized lawyers
        """
        return self.find_all([
            ('is_lawyer', '=', True),
            ('expert_practice_area_ids', 'in', [practice_area_id])
        ])

    def find_lawyers_by_experience(self, min_years):
        """
        Find lawyers with minimum years of experience.

        :param min_years: Minimum years of experience
        :return: Recordset of experienced lawyers
        """
        return self.find_all([
            ('is_lawyer', '=', True),
            ('years_of_experience', '>=', min_years)
        ])

    def find_senior_lawyers(self, min_years=10):
        """
        Find senior lawyers (default: 10+ years experience).

        :param min_years: Minimum years to be considered senior
        :return: Recordset of senior lawyers
        """
        return self.find_lawyers_by_experience(min_years)

    # --- Case-Related Queries ---

    def get_lawyer_case_count(self, lawyer_id, states=None):
        """
        Get count of cases for a lawyer.

        :param lawyer_id: Employee ID
        :param states: Optional list of states to filter (e.g., ['open', 'draft'])
        :return: Integer count
        """
        domain = [('responsible_employee_id', '=', lawyer_id)]

        if states:
            domain.append(('state', 'in', states))

        return self.env['law.case'].search_count(domain)

    def get_lawyer_active_case_count(self, lawyer_id):
        """
        Get count of active cases for a lawyer.

        :param lawyer_id: Employee ID
        :return: Integer count
        """
        return self.get_lawyer_case_count(
            lawyer_id,
            states=['draft', 'open', 'on_hold']
        )

    def get_lawyer_with_lowest_workload(self, practice_area_id=None):
        """
        Find lawyer with lowest current workload.
        Useful for auto-assignment.

        :param practice_area_id: Optional practice area filter
        :return: Lawyer record or None
        """
        lawyers = self.find_available_lawyers(practice_area_id)

        if not lawyers:
            return None

        # Sort by case count (ascending)
        lawyers_with_counts = [
            (lawyer, self.get_lawyer_active_case_count(lawyer.id))
            for lawyer in lawyers
        ]

        lawyers_with_counts.sort(key=lambda x: x[1])

        return lawyers_with_counts[0][0] if lawyers_with_counts else None

    # --- Search & Filter ---

    def search_lawyers_by_name(self, name):
        """
        Search lawyers by name.

        :param name: Name fragment
        :return: Recordset
        """
        return self.find_all([
            ('is_lawyer', '=', True),
            ('name', 'ilike', name)
        ])

    # --- Statistics ---

    def get_lawyer_statistics(self, lawyer_id):
        """
        Get comprehensive statistics for a lawyer.

        :param lawyer_id: Employee ID
        :return: Dictionary with statistics
        """
        lawyer = self.find_by_id(lawyer_id)

        if not lawyer or not lawyer.is_lawyer:
            return {}

        # Get case counts by state
        total_cases = self.env['law.case'].search_count([
            ('responsible_employee_id', '=', lawyer_id)
        ])

        active_cases = self.get_lawyer_active_case_count(lawyer_id)

        closed_cases = self.env['law.case'].search_count([
            ('responsible_employee_id', '=', lawyer_id),
            ('state', '=', 'closed')
        ])

        won_cases = self.env['law.case'].search_count([
            ('responsible_employee_id', '=', lawyer_id),
            ('state', '=', 'closed'),
            ('case_outcome', '=', 'won')
        ])

        return {
            'lawyer_id': lawyer_id,
            'name': lawyer.name,
            'years_of_experience': lawyer.years_of_experience,
            'total_cases': total_cases,
            'active_cases': active_cases,
            'closed_cases': closed_cases,
            'won_cases': won_cases,
            'win_rate': (won_cases / closed_cases * 100) if closed_cases > 0 else 0,
            'specializations': lawyer.expert_practice_area_ids.mapped('name'),
        }

    def get_all_lawyers_statistics(self):
        """
        Get statistics for all lawyers.

        :return: List of dictionaries with statistics
        """
        lawyers = self.find_all_lawyers()
        return [
            self.get_lawyer_statistics(lawyer.id)
            for lawyer in lawyers
        ]
