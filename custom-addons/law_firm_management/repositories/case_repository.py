from .base_repos import BaseRepository
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)

class CaseRepository(BaseRepository):
    def _get_model_name(self):
        return 'law.case'

    def find_all_cases(self, order='create_date desc', limit=None):
        return self.find_all(order=order, limit=limit)

    def find_by_code(self, code):
        """
        Find case by case code.

        :param code: Case code string
        :return: Single case record or empty recordset
        """
        return self.find_one([('code', '=', code)])

    # --- State-Based Queries ---

    def find_cases_by_state(self, state):
        """
        Find all cases in a specific state.

        :param state: State string ('draft', 'open', 'on_hold', 'closed')
        :return: Recordset of cases
        """
        return self.find_all([('state', '=', state)])

    def find_draft_cases(self):
        """Find all draft cases"""
        return self.find_cases_by_state('draft')

    def find_open_cases(self):
        """Find all open/active cases"""
        return self.find_cases_by_state('open')

    def find_on_hold_cases(self):
        """Find all cases on hold"""
        return self.find_cases_by_state('on_hold')

    def find_closed_cases(self, order='close_date desc', limit=None):
        """
        Find all closed cases.

        :param order: Order string
        :param limit: Maximum results
        :return: Recordset of closed cases
        """
        return self.find_all([('state', '=', 'closed')], order=order, limit=limit)

    # --- Lawyer-Related Queries ---

    def find_cases_for_lawyer(self, lawyer_id, state=None):
        """
        Find all cases assigned to a lawyer.

        :param lawyer_id: Employee ID of lawyer
        :param state: Optional state filter
        :return: Recordset of cases
        """
        domain = [('lawyer_ids', 'in', [lawyer_id])]
        if state:
            domain.append(('state', '=', state))
        return self.find_all(domain)

    def find_active_cases_for_lawyer(self, lawyer_id):
        """Find active cases for a specific lawyer"""
        return self.find_cases_for_lawyer(lawyer_id, state='open')

    def find_cases_by_responsible_lawyer(self, lawyer_id, state=None):
        """
        Find cases where lawyer is the responsible attorney.

        :param lawyer_id: Employee ID
        :param state: Optional state filter
        :return: Recordset
        """
        domain = [('responsible_employee_id', '=', lawyer_id)]
        if state:
            domain.append(('state', '=', state))
        return self.find_all(domain)

    def get_lawyer_workload(self, lawyer_id):
        """
        Get workload metrics for a lawyer.

        :param lawyer_id: Employee ID
        :return: Dictionary with counts
        """
        return {
            'total_active': self.count([
                ('lawyer_ids', 'in', [lawyer_id]),
                ('state', '=', 'open')
            ]),
            'as_responsible': self.count([
                ('responsible_employee_id', '=', lawyer_id),
                ('state', '=', 'open')
            ]),
            'total_cases': self.count([('lawyer_ids', 'in', [lawyer_id])]),
        }

    # --- Client-Related Queries ---

    def find_cases_for_client(self, client_id, state=None):
        """
        Find all cases for a specific client.

        :param client_id: Partner ID of client
        :param state: Optional state filter
        :return: Recordset of cases
        """
        domain = [('client_id', '=', client_id)]
        if state:
            domain.append(('state', '=', state))
        return self.find_all(domain, order='create_date desc')

    def find_active_cases_for_client(self, client_id):
        """Find active cases for a client"""
        return self.find_cases_for_client(client_id, state='open')

    def get_client_case_history(self, client_id):
        """
        Get complete case history for a client.

        :param client_id: Partner ID
        :return: Recordset ordered by date
        """
        return self.find_cases_for_client(client_id)

    # --- Practice Area Queries ---

    def find_cases_by_practice_area(self, practice_area_id, state=None):
        """
        Find cases by practice area.

        :param practice_area_id: Practice area ID
        :param state: Optional state filter
        :return: Recordset
        """
        domain = [('practice_area_id', '=', practice_area_id)]
        if state:
            domain.append(('state', '=', state))
        return self.find_all(domain)

    def find_similar_cases(self, case, limit=10):
        """
        Find similar closed cases based on practice area, complexity, and role.

        :param case: law.case record
        :param limit: Maximum results
        :return: Recordset of similar cases
        """
        domain = [
            ('id', '!=', case.id),
            ('state', '=', 'closed'),
        ]

        if case.practice_area_id:
            domain.append(('practice_area_id', '=', case.practice_area_id.id))

        if case.case_complexity:
            domain.append(('case_complexity', '=', case.case_complexity))

        if case.client_role:
            domain.append(('client_role', '=', case.client_role))

        return self.find_all(domain, order='close_date desc', limit=limit)

    def get_practice_area_statistics(self, practice_area_id):
        """
        Get statistics for a practice area.

        :param practice_area_id: Practice area ID
        :return: Dictionary with metrics
        """
        all_cases = self.find_cases_by_practice_area(practice_area_id)
        closed_cases = all_cases.filtered(lambda c: c.state == 'closed')
        won_cases = closed_cases.filtered(lambda c: c.case_outcome == 'won')

        return {
            'total_cases': len(all_cases),
            'open_cases': len(all_cases.filtered(lambda c: c.state == 'open')),
            'closed_cases': len(closed_cases),
            'won_cases': len(won_cases),
            'win_rate': (len(won_cases) / len(closed_cases) * 100) if closed_cases else 0,
        }

    # --- Financial Queries ---

    def find_high_value_cases(self, min_amount, state=None):
        """
        Find cases with claimed amount above threshold.

        :param min_amount: Minimum claimed amount
        :param state: Optional state filter
        :return: Recordset ordered by amount descending
        """
        domain = [('estimated_amount_claim', '>=', min_amount)]
        if state:
            domain.append(('state', '=', state))
        return self.find_all(domain, order='estimated_amount_claim desc')

    def find_profitable_cases(self):
        """Find cases marked as profitable"""
        return self.find_all([('is_profitable', '=', True)])

    def find_cases_by_profitability(self, category):
        """
        Find cases by profitability category.

        :param category: Profitability category string
        :return: Recordset
        """
        return self.find_all([('profitability_category', '=', category)])

    def get_total_claimed_amount(self, domain=None):
        """
        Calculate total claimed amount across cases.

        :param domain: Optional domain filter
        :return: Float total amount
        """
        domain = domain or []
        cases = self.find_all(domain)
        return sum(case.estimated_amount_claim or 0 for case in cases)

    def get_total_recovered_amount(self, domain=None):
        """
        Calculate total recovered amount across closed cases.

        :param domain: Optional domain filter
        :return: Float total amount
        """
        domain = domain or []
        domain.append(('state', '=', 'closed'))
        cases = self.find_all(domain)
        return sum(case.actual_amount_recovered or 0 for case in cases)

    # --- Time-Based Queries ---

    def find_overdue_cases(self):
        """
        Find cases that are overdue (exceeded estimated duration).

        :return: Recordset of overdue cases
        """
        return self.find_all([
            ('state', '=', 'open'),
            ('is_overdue', '=', True)
        ])

    def find_cases_approaching_deadline(self, days=7):
        """
        Find cases approaching their deadline.

        :param days: Days threshold
        :return: Recordset of cases
        """
        return self.find_all([
            ('state', '=', 'open'),
            ('days_remaining', '<=', days),
            ('days_remaining', '>', 0)
        ])

    def find_cases_opened_between(self, start_date, end_date):
        """
        Find cases opened within date range.

        :param start_date: Start date (date object or string)
        :param end_date: End date (date object or string)
        :return: Recordset
        """
        return self.find_all([
            ('open_date', '>=', start_date),
            ('open_date', '<=', end_date)
        ], order='open_date desc')

    def find_cases_closed_between(self, start_date, end_date):
        """
        Find cases closed within date range.

        :param start_date: Start date
        :param end_date: End date
        :return: Recordset
        """
        return self.find_all([
            ('close_date', '>=', start_date),
            ('close_date', '<=', end_date)
        ], order='close_date desc')

    def get_average_case_duration(self, practice_area_id=None):
        """
        Calculate average case duration in days.

        :param practice_area_id: Optional practice area filter
        :return: Float average days
        """
        domain = [
            ('state', '=', 'closed'),
            ('actual_duration_days', '>', 0)
        ]
        if practice_area_id:
            domain.append(('practice_area_id', '=', practice_area_id))

        cases = self.find_all(domain)
        if not cases:
            return 0.0

        total_days = sum(case.actual_duration_days for case in cases)
        return total_days / len(cases)

    # --- Dashboard & Reporting Queries ---

    def get_case_count_by_state(self):
        """
        Get count of cases grouped by state.

        :return: Dictionary {state: count}
        """
        groups = self.read_group(
            domain=[],
            fields=['state'],
            groupby=['state']
        )
        return {group['state']: group['state_count'] for group in groups}

    def get_case_count_by_practice_area(self):
        """
        Get count of cases grouped by practice area.

        :return: List of dictionaries with practice area info and counts
        """
        return self.read_group(
            domain=[],
            fields=['practice_area_id'],
            groupby=['practice_area_id']
        )

    def get_monthly_case_stats(self, year):
        """
        Get case statistics by month for a specific year.

        :param year: Integer year
        :return: Dictionary with monthly data
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        opened = self.find_cases_opened_between(start_date, end_date)
        closed = self.find_cases_closed_between(start_date, end_date)

        return {
            'year': year,
            'total_opened': len(opened),
            'total_closed': len(closed),
            'cases_opened': opened,
            'cases_closed': closed,
        }

    def get_lawyer_performance_metrics(self, lawyer_id):
        """
        Get comprehensive performance metrics for a lawyer.

        :param lawyer_id: Employee ID
        :return: Dictionary with metrics
        """
        all_cases = self.find_cases_for_lawyer(lawyer_id)
        closed_cases = all_cases.filtered(lambda c: c.state == 'closed')
        won_cases = closed_cases.filtered(lambda c: c.case_outcome == 'won')
        open_cases = all_cases.filtered(lambda c: c.state == 'open')
        overdue_cases = open_cases.filtered(lambda c: c.is_overdue)

        return {
            'total_cases': len(all_cases),
            'active_cases': len(open_cases),
            'closed_cases': len(closed_cases),
            'won_cases': len(won_cases),
            'win_rate': (len(won_cases) / len(closed_cases) * 100) if closed_cases else 0,
            'overdue_cases': len(overdue_cases),
            'overdue_rate': (len(overdue_cases) / len(open_cases) * 100) if open_cases else 0,
        }

    # --- Search & Filter Queries ---

    def search_cases_by_code(self, code_fragment):
        """
        Search cases by code fragment.

        :param code_fragment: String to search in code
        :return: Recordset
        """
        return self.find_all([('code', 'ilike', code_fragment)])

    def search_cases_by_client_name(self, name):
        """
        Search cases by client name.

        :param name: Client name fragment
        :return: Recordset
        """
        return self.find_all([('client_id.name', 'ilike', name)])

    def search_cases_by_counterparty(self, name):
        """
        Search cases by counterparty name.

        :param name: Counterparty name fragment
        :return: Recordset
        """
        return self.find_all([('counterparty_id.name', 'ilike', name)])

    def advanced_search(self, filters):
        """
        Advanced search with multiple filters.

        :param filters: Dictionary of filter criteria
        :return: Recordset
        """
        domain = []

        if 'state' in filters:
            domain.append(('state', '=', filters['state']))

        if 'practice_area_id' in filters:
            domain.append(('practice_area_id', '=', filters['practice_area_id']))

        if 'lawyer_id' in filters:
            domain.append(('lawyer_ids', 'in', [filters['lawyer_id']]))

        if 'client_id' in filters:
            domain.append(('client_id', '=', filters['client_id']))

        if 'min_amount' in filters:
            domain.append(('estimated_amount_claim', '>=', filters['min_amount']))

        if 'max_amount' in filters:
            domain.append(('estimated_amount_claim', '<=', filters['max_amount']))

        if 'date_from' in filters:
            domain.append(('create_date', '>=', filters['date_from']))

        if 'date_to' in filters:
            domain.append(('create_date', '<=', filters['date_to']))

        return self.find_all(domain)
