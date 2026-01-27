"""
Practice Area Repository - Centralized data access for practice areas
All practice area queries should go through this repository
"""
from .base_repos import BaseRepository
from .precedent_repository import PrecedentRepository
import logging
from .case_repository import CaseRepository

_logger = logging.getLogger(__name__)


class PracticeAreaRepository(BaseRepository):
    """
    Repository for law.practice.area model.
    Centralizes all practice area related database queries.
    """

    def _get_model_name(self):
        return 'law.practice.area'

    # --- Basic Queries ---

    def find_all_areas(self, order='name asc'):
        """
        Find all practice areas.

        :param order: Order string
        :return: Recordset
        """
        return self.find_all(order=order)

    def find_by_name(self, name):
        """
        Find practice area by exact name.

        :param name: Practice area name
        :return: Single record or empty recordset
        """
        return self.find_one([('name', '=', name)])

    def find_by_code(self, code):
        """
        Find practice area by code.

        :param code: Practice area code (e.g., 'CIV', 'PEN')
        :return: Single record or empty recordset
        """
        return self.find_one([('code', '=', code)])

    # --- Active/Popular Areas ---

    def find_active_areas(self):
        """
        Find active practice areas.
        Assumes there's an 'active' field.

        :return: Recordset
        """
        return self.find_all([('active', '=', True)], order='name asc')

    def get_areas_with_case_count(self):
        """
        Get practice areas with their case counts.

        :return: List of dictionaries with area info and case counts
        """

        case_repo = CaseRepository(self.env)
        areas = self.find_all_areas()
        result = []

        for area in areas:
            # Use repository instead of direct ORM call
            case_count = case_repo.count([
                ('practice_area_id', '=', area.id)
            ])
            result.append({
                'id': area.id,
                'name': area.name,
                'code': area.code,
                'case_count': case_count,
            })

        return sorted(result, key=lambda x: x['case_count'], reverse=True)

    def get_most_common_areas(self, limit=10):
        """
        Get most commonly used practice areas by case count.

        :param limit: Maximum results
        :return: Recordset of practice areas
        """
        areas_with_counts = self.get_areas_with_case_count()
        top_area_ids = [area['id'] for area in areas_with_counts[:limit]]

        return self.find_by_ids(top_area_ids)

    # --- Lawyer-Related Queries ---

    def find_areas_for_lawyer(self, lawyer_id):
        """
        Find practice areas where a lawyer has cases.

        :param lawyer_id: Employee ID
        :return: Recordset of practice areas
        """

        case_repo = CaseRepository(self.env)

        # Get lawyer's cases using repository
        cases = case_repo.find_cases_for_lawyer(lawyer_id)

        # Get unique practice area IDs
        area_ids = list(set(cases.mapped('practice_area_id').ids))
        return self.find_by_ids(area_ids)

    # --- Search Queries ---

    def search_by_name(self, name_fragment):
        """
        Search practice areas by name fragment.

        :param name_fragment: String to search
        :return: Recordset
        """
        return self.find_all([('name', 'ilike', name_fragment)])

    # --- Statistics ---

    def get_area_statistics(self, practice_area_id):
        """
        Get comprehensive statistics for a practice area.

        :param practice_area_id: Practice area ID
        :return: Dictionary with statistics
        """
        case_repo = CaseRepository(self.env)
        precedent_repo = PrecedentRepository(self.env)

        cases = case_repo.find_cases_by_practice_area(practice_area_id)
        closed_cases = cases.filtered(lambda c: c.state == 'closed')
        won_cases = closed_cases.filtered(lambda c: c.case_outcome == 'won')

        precedents = precedent_repo.find_by_practice_area(practice_area_id)

        return {
            'total_cases': len(cases),
            'active_cases': len(cases.filtered(lambda c: c.state == 'open')),
            'closed_cases': len(closed_cases),
            'won_cases': len(won_cases),
            'win_rate': (len(won_cases) / len(closed_cases) * 100) if closed_cases else 0,
            'total_precedents': len(precedents),
            'average_case_duration': sum(c.actual_duration_days or 0 for c in closed_cases) / len(closed_cases) if closed_cases else 0,
        }
