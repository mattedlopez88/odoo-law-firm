"""
Base Repository - Abstract base class for all repositories
Provides common CRUD operations and query patterns
Implements Repository Pattern to decouple data access from business logic
"""
from abc import ABC
import logging

_logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    def __init__(self, env):
        self.env = env
        self._model_name = self._get_model_name()
        self.model = env[self._model_name]

    def _get_model_name(self):
        raise NotImplementedError("Subclasses must implement _get_model_name()")

    # --- CRUD OPERATIONS ---

    def find_by_id(self, record_id):
        if not record_id:
            return self.model.browse([])
        return self.model.browse(record_id)

    def find_by_ids(self, record_ids):
        if not record_ids:
            return self.model.browse([])
        return self.model.browse(record_ids)

    def find_all(self, domain=None, order=None, limit=None, offset=0):
        domain = domain or []
        return self.model.search(domain, order=order, limit=limit, offset=offset)

    def find_one(self, domain):
        return self.model.search(domain, limit=1)

    def create(self, vals):
        return self.model.create(vals)

    def create_many(self, vals_list):
        return self.model.create(vals_list)

    def update(self, record_id, vals):
        record = self.find_by_id(record_id)
        if not record.exists():
            _logger.warning(f"Record {record_id} not found for update in {self._model_name}")
            return False
        return record.write(vals)

    def update_many(self, domain, vals):
        records = self.find_all(domain)
        if records:
            records.write(vals)
        return len(records)

    def delete(self, record_id):
        record = self.find_by_id(record_id)
        if not record.exists():
            _logger.warning(f"Record {record_id} not found for deletion in {self._model_name}")
            return False
        return record.unlink()

    def delete_many(self, domain):
        records = self.find_all(domain)
        count = len(records)
        if records:
            records.unlink()
        return count

    # --- Query Utilities ---

    def count(self, domain=None):
        domain = domain or []
        return self.model.search_count(domain)

    def exists(self, record_id):
        record = self.find_by_id(record_id)
        return record.exists()

    def exists_with_domain(self, domain):
        return self.count(domain) > 0

    def get_field_value(self, record_id, field_name):
        record = self.find_by_id(record_id)
        if not record.exists():
            return None
        return getattr(record, field_name, None)

    def search_read(self, domain=None, fields=None, order=None, limit=None, offset=0):
        """
        Search and read records (returns dictionaries instead of recordset).
        More efficient when you don't need the full ORM functionality.

        :param domain: Odoo domain
        :param fields: List of field names to read
        :param order: Order string
        :param limit: Maximum number of records
        :param offset: Number of records to skip
        :return: List of dictionaries
        """
        domain = domain or []
        return self.model.search_read(domain, fields=fields, order=order, limit=limit, offset=offset)

    # --- Bulk Operations ---

    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
        Perform a read_group query for aggregations.

        :param domain: Odoo domain
        :param fields: List of field names
        :param groupby: List of fields to group by
        :param offset: Number of groups to skip
        :param limit: Maximum number of groups
        :param orderby: Order string
        :param lazy: Whether to load records lazily
        :return: List of group dictionaries
        """
        return self.model.read_group(
            domain=domain,
            fields=fields,
            groupby=groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy
        )

    # --- Name Search ---

    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """
        Search records by name.

        :param name: Name to search for
        :param domain: Additional domain filters
        :param operator: Search operator ('ilike', '=', etc.)
        :param limit: Maximum results
        :return: List of tuples (id, display_name)
        """
        domain = domain or []
        return self.model.name_search(name=name, args=domain, operator=operator, limit=limit)
