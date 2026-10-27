# Candidate Brief: ShipStream Inventory Allocator
**Assessment ID:** `BH-L2-002`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the fulfillment engineering team at **ShipStream**. We maintain the inventory reservation and allocation engines that route customer order lines to our nationwide network of distribution centers.

Recently, our warehouse inventory audits revealed discrepancies:
- Items that customers attempted to purchase but abandoned due to partial out-of-stock items remain locked in a "reserved" status.
- Products show as "Sold Out" on the website even though physical units are sitting unsold on warehouse shelves.

You are tasked with investigating our multi-warehouse allocation engine, fixing the inventory leakage bug, and verifying complete rollback protection.

---

## Your Objectives

1. **Investigate the Codebase:**
   - Inspect:
     - `src/models.py`: Data classes (`OrderLine`, `ReservationRecord`, `AllocationResult`).
     - `src/exceptions.py`: Exceptions (`InsufficientStockError`, `AllocationError`).
     - `src/warehouse.py`: Physical warehouse class managing available vs. reserved stock.
     - `src/allocation_service.py`: Service orchestrator.
2. **Reproduce the Defect:**
   - Run the test suite:
     ```bash
     python3 -m unittest discover tests
     ```
   - Observe failures in `test_bug_reproduction_ticket_ship_301_zombie_reservation_on_partial_failure` and `test_bug_reproduction_ticket_ship_302_invalid_line_item_rollbacks_prior_reservations`.
3. **Diagnose Root Cause:**
   - Trace what happens when `allocate_order()` successfully reserves stock for the first line item, but encounters an error on a subsequent line item.
4. **Implement Transactional Rollback:**
   - Ensure that if any line item cannot be fulfilled or fails validation, **all units reserved during that order attempt are immediately released back to their respective warehouses**.
   - Available stock must return to its pre-order level.
   - Reserved stock must return to its pre-order level.
   - Re-raise an `AllocationError` explaining the failure.
5. **Expand Test Coverage:**
   - Add new tests to `tests/test_allocation_service.py` verifying:
     - Multi-warehouse chain failures (e.g. 3 warehouses where line 3 fails).
     - Sequential orders (order 1 succeeds, order 2 fails & rolls back, order 3 succeeds).
     - Edge cases such as exact stock depletion.
6. **Submit Documentation:**
   - Fill out [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-2-intermediate/task-2-inventory-allocator/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Python 3 Standard Library only.
- Do not modify `warehouse.py` method signatures (`reserve` and `release`).
- Ensure all reservations made during a failed order are cleanly rolled back.
