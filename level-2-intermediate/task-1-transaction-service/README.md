# Candidate Brief: FinPulse Transaction Summary Service
**Assessment ID:** `BH-L2-001`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the Core Banking Ledger engineering team at **FinPulse**. We maintain the financial data pipeline responsible for generating account transaction summaries, customer statement figures, and ledger audit reports.

Recently, our Banking Operations and Customer Support teams escalated two urgent tickets:
- **Ticket #FIN-201:** Customers with pending check deposits or card pre-authorization holds see their monthly statement inflow and outflow totals inflated. An unverified check of $1,000.00 is erroneously reflected as settled cash!
- **Ticket #FIN-202:** Cancelled wire transfers are erroneously contributing to account activity metrics.

You are tasked with investigating the multi-file architecture, locating where transaction status filtering breaks down, implementing a robust fix, and protecting our banking ledger from regressions.

---

## Your Objectives

1. **Investigate the Multi-Module Architecture:**
   - Explore `src/`:
     - `models.py`: Domain entities (`Transaction`, `AccountSummary`, `TransactionType`, `TransactionStatus`).
     - `repository.py`: In-memory storage and parameterized query interface.
     - `calculator.py`: Mathematical calculation engine.
     - `service.py`: High-level service orchestrating repository lookups and calculations.
2. **Reproduce the Defect:**
   - Run the test suite:
     ```bash
     python3 -m unittest discover tests
     ```
   - Observe the failures in `test_bug_reproduction_ticket_fin_201_pending_transactions_included` and `test_bug_reproduction_ticket_fin_202_cancelled_transactions_included`.
3. **Trace Component Interactions & Diagnose Root Cause:**
   - Analyze how `TransactionSummaryService` interacts with `TransactionRepository` and `SummaryCalculator`.
   - Why do `PENDING` and `CANCELLED` transactions leak into customer summaries?
4. **Implement an Architecturally Sound Fix:**
   - Adhere strictly to the business rules:
     - Only `COMPLETED` transactions contribute to `total_inflow`, `total_outflow`, `net_balance`, and `transaction_count`.
     - `PENDING`, `FAILED`, and `CANCELLED` transactions must **never** contribute to settled account metrics.
     - An account with zero transactions must produce a valid empty summary (`0.00` amounts and `0` count).
     - Maintain defense-in-depth across the service layer and calculator.
5. **Expand Test Coverage:**
   - Add automated unit tests to `tests/test_summary_service.py` verifying:
     - Mixed transaction accounts containing all statuses.
     - Date range boundary filtering (`start_date` and `end_date`).
     - Accounts with only debit or only credit transactions.
     - Input validation errors (invalid account IDs, inverted date ranges).
6. **Submit Documentation:**
   - Fill out [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-2-intermediate/task-1-transaction-service/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Do not introduce external dependencies. Use Python 3 Standard Library only.
- Do not alter the public interfaces of dataclasses or required methods.
- Document your technical decisions clearly in `CANDIDATE_SUBMISSION.md`.
