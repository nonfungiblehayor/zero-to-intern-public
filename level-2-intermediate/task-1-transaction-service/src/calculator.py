from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from models import Transaction, TransactionType, TransactionStatus, AccountSummary


class SummaryCalculator:
    """Calculates financial inflow, outflow, and net balance summaries for transactions."""

    def calculate(
        self,
        account_id: str,
        transactions: List[Transaction],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AccountSummary:
        """
        Aggregates transaction list into an AccountSummary.
        """
        total_inflow = Decimal("0.00")
        total_outflow = Decimal("0.00")
        count = 0

        for tx in transactions:
            # Filter out failed transactions
            if tx.status == TransactionStatus.FAILED:
                continue

            if tx.transaction_type == TransactionType.CREDIT:
                total_inflow += tx.amount
            elif tx.transaction_type == TransactionType.DEBIT:
                total_outflow += tx.amount

            count += 1

        net_balance = total_inflow - total_outflow

        return AccountSummary(
            account_id=account_id,
            total_inflow=total_inflow.quantize(Decimal("0.01")),
            total_outflow=total_outflow.quantize(Decimal("0.01")),
            net_balance=net_balance.quantize(Decimal("0.01")),
            transaction_count=count,
            start_date=start_date,
            end_date=end_date
        )
