"""
Precedent Analysis Service
Centralized service for precedent search and favorability analysis
Eliminates code duplication between compute methods
"""
from ..repositories.precedent_repository import PrecedentRepository
from ..repositories.case_repository import CaseRepository
import logging

_logger = logging.getLogger(__name__)

class PrecedentAnalysisService:
    """
    Service for precedent search and analysis.
    Single Responsibility: All precedent-related logic in one place.
    """

    def __init__(self, env):
        self.env = env
        self.precedent_repo = PrecedentRepository(env)
        self.case_repo = CaseRepository(env)

    def find_relevant_precedents(self, practice_area_id, filters=None):
        """
        Find precedents for a practice area with optional filters.
        Centralized search logic to avoid duplication.

        :param practice_area_id: ID of practice area
        :param filters: Optional list of additional domain filters
        :return: Recordset of law.case.precedent
        """
        if not practice_area_id:
            return self.precedent_repo.model.browse([])

        precedents = self.precedent_repo.find_by_practice_area(
            practice_area_id,
            additional_filters=filters
        )

        _logger.debug(
            f"Found {len(precedents)} precedents for practice area {practice_area_id}"
        )

        return precedents

    def analyze_favorability(self, precedents, client_role):
        """
        Analyze how precedents favor the client role.

        :param precedents: Recordset of law.case.precedent
        :param client_role: 'plaintiff' or 'defendant'
        :return: Dictionary with analysis results
        """
        if not precedents or not client_role:
            return {
                'favorable': self.precedent_repo.model.browse([]),
                'unfavorable': self.precedent_repo.model.browse([]),
                'neutral': self.precedent_repo.model.browse([]),
                'favorable_count': 0,
                'unfavorable_count': 0,
                'neutral_count': 0,
                'favorable_ratio': 0.0,
            }

        # Filter precedents by favorability
        favorable = precedents.filtered(lambda p: p.favoured_party == client_role)
        unfavorable = precedents.filtered(
            lambda p: p.favoured_party and p.favoured_party != client_role
        )
        neutral = precedents - favorable - unfavorable

        total = len(precedents)
        favorable_count = len(favorable)
        unfavorable_count = len(unfavorable)
        neutral_count = len(neutral)

        # Calculate favorability ratio
        ratio = (favorable_count / total * 100) if total > 0 else 0.0

        _logger.debug(
            f"Precedent analysis: {favorable_count} favorable, "
            f"{unfavorable_count} unfavorable, {neutral_count} neutral "
            f"(ratio: {ratio:.1f}%)"
        )

        return {
            'favorable': favorable,
            'unfavorable': unfavorable,
            'neutral': neutral,
            'favorable_count': favorable_count,
            'unfavorable_count': unfavorable_count,
            'neutral_count': neutral_count,
            'favorable_ratio': ratio,
        }

    def get_similar_cases(self, case, limit=10):
        """
        Find similar closed cases based on multiple criteria.
        Useful for precedent research and success rate estimation.
        Delegates to CaseRepository.

        :param case: law.case record
        :param limit: Maximum number of cases to return
        :return: Recordset of law.case
        """
        similar_cases = self.case_repo.find_similar_cases(case, limit=limit)

        _logger.debug(
            f"Found {len(similar_cases)} similar cases for case {case.code or case.id}"
        )

        return similar_cases

    def calculate_success_probability(self, similar_cases):
        """
        Calculate success probability based on similar case outcomes.

        :param similar_cases: Recordset of closed law.case records
        :return: Dictionary with success metrics
        """
        if not similar_cases:
            return {
                'success_rate': 0.0,
                'won_count': 0,
                'lost_count': 0,
                'settled_count': 0,
                'total_count': 0,
            }

        won = similar_cases.filtered(lambda c: c.case_outcome == 'won')
        lost = similar_cases.filtered(lambda c: c.case_outcome == 'lost')
        settled = similar_cases.filtered(lambda c: c.case_outcome == 'settled')

        total = len(similar_cases)
        won_count = len(won)

        success_rate = (won_count / total * 100) if total > 0 else 0.0

        return {
            'success_rate': success_rate,
            'won_count': won_count,
            'lost_count': len(lost),
            'settled_count': len(settled),
            'total_count': total,
        }

    def get_precedent_summary(self, practice_area_id, client_role):
        """
        Get complete precedent summary for a practice area and client role.
        Combines search and analysis in one call.

        :param practice_area_id: ID of practice area
        :param client_role: 'plaintiff' or 'defendant'
        :return: Dictionary with complete analysis
        """
        precedents = self.find_relevant_precedents(practice_area_id)
        analysis = self.analyze_favorability(precedents, client_role)

        return {
            'total_precedents': len(precedents),
            'favorable_count': analysis['favorable_count'],
            'unfavorable_count': analysis['unfavorable_count'],
            'neutral_count': analysis['neutral_count'],
            'favorable_ratio': analysis['favorable_ratio'],
            'has_favorable': analysis['favorable_count'] > 0,
            'precedents': precedents,
            'favorable_precedents': analysis['favorable'],
            'unfavorable_precedents': analysis['unfavorable'],
        }
