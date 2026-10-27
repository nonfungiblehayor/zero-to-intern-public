import unittest
from decimal import Decimal
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import Transaction, TransactionType, TransactionStatus
from repository import TransactionRepository
from calculator import SummaryCalculator
from service import TransactionSummaryService


class TestTransactionSummaryService(unittest.TestCase):

    def setUp(self):
        self.repository = TransactionRepository()
        self.calculator = SummaryCalculator()
        self.service = TransactionSummaryService(self.repository, self.calculator)

    def test_account_with_only_completed_transactions(self):
        """Baseline test: All transactions are completed."""
        account_id = "ACC-001"
        self.repository.add(Transaction(
            id="TX-1",
            account_id=account_id,
            amount=Decimal("200.00"),
            transaction_type=TransactionType.CREDIT,
            status=TransactionStatus.COMPLETED,
            created_at=datetime(2026, 1, 10, 10, 0)
        ))
        self.repository.add(Transaction(
            id="TX-2",
            account_id=account_id,
            amount=Decimal("50.00"),
            transaction_type=TransactionType.DEBIT,
            status=TransactionStatus.COMPLETED,
            created_at=datetime(2026, 1, 15, 14, 30)
        ))

        summary = self.service.get_account_summary(account_id)
        self.assertEqual(summary.account_id, account_id)
        self.assertEqual(summary.total_inflow, Decimal("200.00"))
        self.assertEqual(summary.total_outflow, Decimal("50.00"))
        self.assertEqual(summary.net_balance, Decimal("150.00"))
        self.assertEqual(summary.transaction_count, 2)

    def test_empty_account_summary(self):
        """An account with no transactions produces a valid empty summary."""
        summary = self.service.get_account_summary("ACC-EMPTY")
        self.assertEqual(summary.total_inflow, Decimal("0.00"))
        self.assertEqual(summary.total_outflow, Decimal("0.00"))
        self.assertEqual(summary.net_balance, Decimal("0.00"))
        self.assertEqual(summary.transaction_count, 0)

    def test_bug_reproduction_ticket_fin_201_pending_transactions_included(self):
        """
        REPRODUCTION TEST 1 (Ticket #FIN-201):
        Pending deposits and debit holds must NOT contribute to settled totals.
        Under the bug, pending items leak into the summary!
        """
        account_id = "ACC-PENDING-TEST"
        # Completed deposit
        self.repository.add(Transaction(
            id="TX-C1",
            account_id=account_id,
            amount=Decimal("500.00"),
            transaction_type=TransactionType.CREDIT,
            status=TransactionStatus.COMPLETED,
            created_at=datetime(2026, 1, 5, 9, 0)
        ))
        # Completed debit
        self.repository.add(Transaction(
            id="TX-C2",
            account_id=account_id,
            amount=Decimal("120.00"),
            transaction_type=TransactionType.DEBIT,
            status=TransactionStatus.COMPLETED,
            created_at=datetime(2026, 1, 6, 11, 0)
        ))
        # Pending check deposit (should NOT count as settled cash)
        self.repository.add(Transaction(
            id="TX-P1",
            account_id=account_id,
            amount=Decimal("1000.00"),
            transaction_type=TransactionType.CREDIT,
            status=TransactionStatus.PENDING,
            created_at=datetime(2026, 1, 7, 16, 0)
        ))
        # Pending debit hold (should NOT count as settled debit)
        self.repository.add(Transaction(
            id="TX-P2",
            account_id=account_id,
            amount=Decimal("45.00"),
            transaction_type=TransactionType.DEBIT,
            status=TransactionStatus.PENDING,
            created_at=datetime(2026, 1, 8, 12, 0)
        ))

        summary = self.service.get_account_summary(account_id)
        self.assertEqual(summary.total_inflow, Decimal("500.00"), "Pending deposit leaked into inflow!")
        self.assertEqual(summary.total_outflow, Decimal("120.00"), "Pending debit leaked into outflow!")
        self.assertEqual(summary.net_balance, Decimal("380.00"), "Net balance calculated incorrectly due to pending items!")
        self.assertEqual(summary.transaction_count, 2, "Transaction count included pending transactions!")

    def test_bug_reproduction_ticket_fin_202_cancelled_transactions_included(self):
        """
        REPRODUCTION TEST 2 (Ticket #FIN-202):
        Cancelled transactions must NOT contribute to settled totals.
        """
        account_id = "ACC-CANCELLED-TEST"
        self.repository.add(Transaction(
            id="TX-OK",
            account_id=account_id,
            amount=Decimal("100.00"),
            transaction_type=TransactionType.CREDIT,
            status=TransactionStatus.COMPLETED,
            created_at=datetime(2026, 1, 1, 10, 0)
        ))
        self.repository.add(Transaction(
            id="TX-CANCEL",
            account_id=account_id,
            amount=Decimal("300.00"),
            transaction_type=TransactionType.CREDIT,
            status=TransactionStatus.CANCELLED,
            created_at=datetime(2026, 1, 2, 10, 0)
        ))

        summary = self.service.get_account_summary(account_id)
        self.assertEqual(summary.total_inflow, Decimal("100.00"), "Cancelled transaction counted in total inflow!")
        self.assertEqual(summary.transaction_count, 1)


if __name__ == "__main__":
    unittest.main()
