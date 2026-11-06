# Candidate Brief: ShipStream Inventory Allocator
**Assessment ID:** `BH-L2-002`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the fulfillment engineering team at **ShipStream**. We maintain the inventory reservation and allocation engines that route customer order lines to our nationwide network of distribution centers.

Recently, our warehouse inventory audits revealed critical discrepancies:
- Items that customers attempted to purchase but abandoned due to partial out-of-stock items remain locked in a "reserved" status.
- Products show as "Sold Out" on the website even though physical units are sitting unsold on warehouse shelves.

You are tasked with investigating our multi-warehouse allocation engine, fixing the inventory leakage bug, and verifying complete rollback protection.

---

## Running the Backend Service & Endpoints

This is a **Backend Service with REST API Endpoints**. You can run the live service and test allocation endpoints directly, as well as execute the unit test suite.

### 1. Launch the API Server:
```bash
python3 api.py
```
*Server runs on `http://localhost:8000` (FastAPI / Swagger docs at `/docs` if requirements installed).*

### 2. Inspect Initial Inventory:
```bash
curl http://localhost:8000/api/warehouses
```

### 3. Trigger a Partial-Failure Order Allocation:
```bash
curl -X POST http://localhost:8000/api/inventory/allocate \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-BUG", "lines": [{"sku": "SKU-LAPTOP", "quantity": 2}, {"sku": "SKU-MOUSE", "quantity": 100}]}'
```
Query `/api/warehouses` again to observe the leaked reservation in the starter code.

### 4. CLI Unit Tests:
```bash
python3 -m unittest discover tests
```
Observe failures in `test_bug_reproduction_ticket_ship_301_zombie_reservation_on_partial_failure` and `test_bug_reproduction_ticket_ship_302_invalid_line_item_rollbacks_prior_reservations`.

---

## Your Objectives

1. **Investigate the Codebase:**
   - Inspect:
     - `src/models.py`: Data classes (`OrderLine`, `ReservationRecord`, `AllocationResult`).
     - `src/exceptions.py`: Exceptions (`InsufficientStockError`, `AllocationError`).
     - `src/warehouse.py`: Physical warehouse class managing available vs. reserved stock.
     - `src/allocation_service.py`: Service orchestrator.
2. **Diagnose Root Cause:**
   - Trace what happens when `allocate_order()` successfully reserves stock for the first line item, but encounters an error on a subsequent line item.
3. **Implement Transactional Rollback:**
   - Ensure that if any line item cannot be fulfilled or fails validation, **all units reserved during that order attempt are immediately released back to their respective warehouses**.
   - Available stock must return to its pre-order level.
   - Reserved stock must return to its pre-order level.
   - Re-raise an `AllocationError` explaining the failure.
4. **Expand Test Coverage:**
   - Add new tests to `tests/test_allocation_service.py` verifying:
     - Multi-warehouse chain failures (e.g. 3 warehouses where line 3 fails).
     - Sequential orders (order 1 succeeds, order 2 fails & rolls back, order 3 succeeds).
     - Edge cases such as exact stock depletion.
5. **Prepare for Mentor Review:**
   - Be prepared to discuss distributed transactions, compensation/rollback patterns, and idempotency during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only.
- Do not modify `warehouse.py` method signatures (`reserve` and `release`).
- Ensure all reservations made during a failed order are cleanly rolled back.
