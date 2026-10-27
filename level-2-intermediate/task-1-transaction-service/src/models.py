from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


class TransactionType(str, Enum):
    CREDIT = "CREDIT"   # Money deposited or received
    DEBIT = "DEBIT"     # Money withdrawn or paid out


class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Transaction:
    id: str
    account_id: str
    amount: Decimal
    transaction_type: TransactionType
    status: TransactionStatus
    created_at: datetime
    description: str = ""


@dataclass
class AccountSummary:
    account_id: str
    total_inflow: Decimal
    total_outflow: Decimal
    net_balance: Decimal
    transaction_count: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
