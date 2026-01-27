"""
Follower Observer - Manages case followers based on lawyer assignments
Replaces the _update_followers() method logic in law_case.py
"""
from ..case_event_manager import CaseEventObserver
from ...repositories.lawyer_repository import LawyerRepository
import logging

_logger = logging.getLogger(__name__)

class FollowerObserver(CaseEventObserver):

    def __init__(self, env):
        super().__init__(env)
        self.lawyer_repo = LawyerRepository(env)

    def get_priority(self):
        return 10

    def can_handle(self, event):
        """Handle lawyer assignment and case creation events"""
        return event.event_type in [
            'case_created',
            'lawyer_assigned',
            'case_updated'
        ]

    def handle(self, event):
        """
        Update case followers based on lawyer assignments.

        :param event: CaseEvent instance
        """
        case = event.case

        if event.event_type == 'case_created':
            self._add_initial_followers(case)

        elif event.event_type == 'lawyer_assigned':
            self._handle_lawyer_change(case, event)

        elif event.event_type == 'case_updated':
            # Check if lawyer_ids changed
            if 'lawyer_ids' in event.get_changed_fields():
                self._sync_followers_with_lawyers(case)

    def _add_initial_followers(self, case):
        """Add initial followers when case is created"""
        if not case.lawyer_ids:
            return

        partners_to_follow = self._get_lawyer_partners(case.lawyer_ids)
        if partners_to_follow:
            case.message_subscribe(partner_ids=partners_to_follow.ids)
            _logger.info(
                f"Added {len(partners_to_follow)} initial followers to case {case.code}"
            )

    def _handle_lawyer_change(self, case, event):
        """
        Handle responsible lawyer change.
        Uses LawyerRepository instead of direct ORM calls.
        """
        old_lawyer_id = event.get_old_value('responsible_employee_id')
        new_lawyer_id = event.get_new_value('responsible_employee_id')

        if old_lawyer_id:
            old_lawyer = self.lawyer_repo.find_by_id(old_lawyer_id)
            if old_lawyer and old_lawyer not in case.lawyer_ids:
                self._remove_lawyer_as_follower(case, old_lawyer)

        if new_lawyer_id:
            new_lawyer = self.lawyer_repo.find_by_id(new_lawyer_id)
            if new_lawyer:
                self._add_lawyer_as_follower(case, new_lawyer)

    def _sync_followers_with_lawyers(self, case):
        """
        Synchronize followers with current lawyer team.
        Replaces the logic from _update_followers() in law_case.py
        """
        # Get current lawyer users
        lawyer_users = case.lawyer_ids.mapped('user_id')
        current_followers = case.message_partner_ids

        # Find lawyers to remove (followers who are lawyers but not in team)
        lawyers_to_remove = current_followers.filtered(
            lambda p: p.user_ids and
            p.user_ids[0] not in lawyer_users and
            self._is_lawyer_partner(p)
        )

        if lawyers_to_remove:
            case.message_unsubscribe(partner_ids=lawyers_to_remove.ids)
            _logger.info(
                f"Removed {len(lawyers_to_remove)} followers from case {case.code}"
            )

        # Add new lawyers as followers
        lawyer_partners = self._get_lawyer_partners(case.lawyer_ids)
        partners_to_add = lawyer_partners - current_followers

        if partners_to_add:
            case.message_subscribe(partner_ids=partners_to_add.ids)
            _logger.info(
                f"Added {len(partners_to_add)} followers to case {case.code}"
            )

    def _add_lawyer_as_follower(self, case, lawyer):
        if lawyer.user_id and lawyer.user_id.partner_id:
            case.message_subscribe(partner_ids=[lawyer.user_id.partner_id.id])
            _logger.debug(f"Added lawyer {lawyer.name} as follower to case {case.code}")

    def _remove_lawyer_as_follower(self, case, lawyer):
        if lawyer.user_id and lawyer.user_id.partner_id:
            case.message_unsubscribe(partner_ids=[lawyer.user_id.partner_id.id])
            _logger.debug(f"Removed lawyer {lawyer.name} as follower from case {case.code}")

    def _get_lawyer_partners(self, lawyers):
        """Get partner records for lawyers"""
        return lawyers.mapped('user_id.partner_id').filtered(lambda p: p)

    def _is_lawyer_partner(self, partner):
        """
        Check if a partner is associated with a lawyer.
        Uses LawyerRepository instead of direct search.
        """
        if not partner.user_ids:
            return False

        # Use repository to find lawyer by user_id
        lawyer = self.lawyer_repo.find_lawyer_by_user_id(partner.user_ids[0].id)
        return bool(lawyer)
