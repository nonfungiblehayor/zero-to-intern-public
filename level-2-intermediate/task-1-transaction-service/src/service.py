from typing import Optional
from datetime import datetime
from repository import TransactionRepository
from calculator import SummaryCalculator
from models import AccountSummary


class TransactionSummaryService:
    """Orchestrates transaction retrieval and summary aggregation for customer accounts."""

    def __init__(self, repository: TransactionRepository, calculator: SummaryCalculator):
        self.repository = repository
        self.calculator = calculator

    def get_account_summary(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AccountSummary:
        """
        Retrieves transactions for an account within an optional date range
        and calculates the account financial summary.
        """
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id must be a non-empty string.")

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date cannot be after end_date.")

        transactions = self.repository.find_by_account(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )

        return self.calculator.calculate(
            account_id=account_id,
            transactions=transactions,
            start_date=start_date,
            end_date=end_date
        )
