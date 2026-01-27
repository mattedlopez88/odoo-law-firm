"""
Precedent Repository - Centralized data access for legal precedents
All precedent queries should go through this repository
"""
from .base_repos import BaseRepository
import logging

_logger = logging.getLogger(__name__)


class PrecedentRepository(BaseRepository):
    """
    Repository for law.case.precedent model.
    Centralizes all precedent-related database queries.
    """

    def _get_model_name(self):
        return 'law.case.precedent'

    # --- Basic Precedent Queries ---

    def find_all_precedents(self, order='create_date desc', limit=None):
        """Find all precedents with optional ordering and limit"""
        return self.find_all(order=order, limit=limit)

    # --- Practice Area Queries ---

    def find_by_practice_area(self, practice_area_id, additional_filters=None):
        """
        Find precedents for a specific practice area.

        :param practice_area_id: Practice area ID
        :param additional_filters: Optional list of additional domain tuples
        :return: Recordset of precedents
        """
        domain = [('practice_area_id', '=', practice_area_id)]

        if additional_filters:
            domain.extend(additional_filters)

        return self.find_all(domain)

    def find_favorable_for_role(self, practice_area_id, client_role):
        """
        Find precedents favorable to a specific party role.

        :param practice_area_id: Practice area ID
        :param client_role: 'plaintiff' or 'defendant'
        :return: Recordset of favorable precedents
        """
        return self.find_all([
            ('practice_area_id', '=', practice_area_id),
            ('favoured_party', '=', client_role)
        ])

    def find_unfavorable_for_role(self, practice_area_id, client_role):
        """
        Find precedents unfavorable to a specific party role.

        :param practice_area_id: Practice area ID
        :param client_role: 'plaintiff' or 'defendant'
        :return: Recordset of unfavorable precedents
        """
        opposing_role = 'defendant' if client_role == 'plaintiff' else 'plaintiff'
        return self.find_all([
            ('practice_area_id', '=', practice_area_id),
            ('favoured_party', '=', opposing_role)
        ])

    # --- Court & Jurisdiction Queries ---

    def find_by_court_level(self, court_level):
        """
        Find precedents by court level.

        :param court_level: Court level string
        :return: Recordset
        """
        return self.find_all([('court_level', '=', court_level)])

    def find_by_jurisdiction(self, jurisdiction):
        """
        Find precedents by jurisdiction.

        :param jurisdiction: Jurisdiction string
        :return: Recordset
        """
        return self.find_all([('jurisdiction', '=', jurisdiction)])

    # --- Recent & Popular Queries ---

    def find_recent_precedents(self, practice_area_id=None, limit=10):
        """
        Find most recent precedents.

        :param practice_area_id: Optional practice area filter
        :param limit: Maximum results
        :return: Recordset ordered by date
        """
        domain = []
        if practice_area_id:
            domain.append(('practice_area_id', '=', practice_area_id))

        return self.find_all(domain, order='precedent_date desc', limit=limit)

    def find_most_cited_precedents(self, practice_area_id=None, limit=10):
        """
        Find most frequently used precedents.

        :param practice_area_id: Optional practice area filter
        :param limit: Maximum results
        :return: Recordset
        """
        # Assuming there's a citation_count field
        domain = []
        if practice_area_id:
            domain.append(('practice_area_id', '=', practice_area_id))

        return self.find_all(domain, order='citation_count desc', limit=limit)

    # --- Search Queries ---

    def search_by_case_name(self, case_name):
        """
        Search precedents by case name.

        :param case_name: Case name fragment
        :return: Recordset
        """
        return self.find_all([('case_name', 'ilike', case_name)])

    def search_by_keywords(self, keywords):
        """
        Search precedents by keywords.

        :param keywords: List of keyword strings or single string
        :return: Recordset
        """
        if isinstance(keywords, str):
            keywords = [keywords]

        domain = []
        for keyword in keywords:
            domain.append('|')
            domain.append(('case_name', 'ilike', keyword))
            domain.append(('summary', 'ilike', keyword))

        # Remove the first '|' if it exists
        if domain and domain[0] == '|':
            domain = domain[1:]

        return self.find_all(domain)

    # --- Statistics & Aggregations ---

    def get_precedent_count_by_practice_area(self):
        """
        Get count of precedents grouped by practice area.

        :return: List of dictionaries with practice area and counts
        """
        return self.read_group(
            domain=[],
            fields=['practice_area_id'],
            groupby=['practice_area_id']
        )

    def get_precedent_count_by_jurisdiction(self):
        """
        Get count of precedents grouped by jurisdiction.

        :return: List of dictionaries
        """
        return self.read_group(
            domain=[],
            fields=['jurisdiction'],
            groupby=['jurisdiction']
        )

    def get_favorability_stats(self, practice_area_id):
        """
        Get favorability statistics for a practice area.

        :param practice_area_id: Practice area ID
        :return: Dictionary with stats
        """
        all_precedents = self.find_by_practice_area(practice_area_id)
        plaintiff_favorable = all_precedents.filtered(lambda p: p.favoured_party == 'plaintiff')
        defendant_favorable = all_precedents.filtered(lambda p: p.favoured_party == 'defendant')

        total = len(all_precedents)

        return {
            'total_precedents': total,
            'plaintiff_favorable': len(plaintiff_favorable),
            'defendant_favorable': len(defendant_favorable),
            'plaintiff_ratio': (len(plaintiff_favorable) / total * 100) if total > 0 else 0,
            'defendant_ratio': (len(defendant_favorable) / total * 100) if total > 0 else 0,
        }

    # --- Advanced Filters ---

    def find_by_date_range(self, start_date, end_date, practice_area_id=None):
        """
        Find precedents within a date range.

        :param start_date: Start date
        :param end_date: End date
        :param practice_area_id: Optional practice area filter
        :return: Recordset
        """
        domain = [
            ('precedent_date', '>=', start_date),
            ('precedent_date', '<=', end_date)
        ]

        if practice_area_id:
            domain.append(('practice_area_id', '=', practice_area_id))

        return self.find_all(domain, order='precedent_date desc')

    def advanced_search(self, filters):
        """
        Advanced search with multiple filters.

        :param filters: Dictionary of filter criteria
        :return: Recordset
        """
        domain = []

        if 'practice_area_id' in filters:
            domain.append(('practice_area_id', '=', filters['practice_area_id']))

        if 'favoured_party' in filters:
            domain.append(('favoured_party', '=', filters['favoured_party']))

        if 'jurisdiction' in filters:
            domain.append(('jurisdiction', '=', filters['jurisdiction']))

        if 'court_level' in filters:
            domain.append(('court_level', '=', filters['court_level']))

        if 'date_from' in filters:
            domain.append(('precedent_date', '>=', filters['date_from']))

        if 'date_to' in filters:
            domain.append(('precedent_date', '<=', filters['date_to']))

        if 'case_name' in filters:
            domain.append(('case_name', 'ilike', filters['case_name']))

        return self.find_all(domain)
