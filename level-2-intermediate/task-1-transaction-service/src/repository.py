from typing import List, Optional
from datetime import datetime
from models import Transaction, TransactionStatus


class TransactionRepository:
    """In-memory data store simulating persistence operations for account transactions."""

    def __init__(self):
        self._storage: List[Transaction] = []

    def add(self, transaction: Transaction) -> None:
        self._storage.append(transaction)

    def find_by_account(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[TransactionStatus] = None
    ) -> List[Transaction]:
        """
        Finds transactions matching an account ID with optional date and status filters.
        Note: When status is omitted (None), returns transactions across all statuses.
        """
        results = [tx for tx in self._storage if tx.account_id == account_id]

        if start_date:
            results = [tx for tx in results if tx.created_at >= start_date]

        if end_date:
            results = [tx for tx in results if tx.created_at <= end_date]

        if status:
            results = [tx for tx in results if tx.status == status]

        return results
