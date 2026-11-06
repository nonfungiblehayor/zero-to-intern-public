# Candidate Brief: CacheSync Distributed Cache Coherence
**Assessment ID:** `BH-L3-002`  
**[CANDIDATE MATERIAL]**

---

## Welcome to CacheSync

Welcome to the Core Storage & Caching infrastructure team at **CacheSync**. We maintain the in-memory write-through cache tier fronting high-throughput database clusters. The cache tier manages LRU eviction, time-to-live (TTL) expiration, and an asynchronous/buffered write queue to minimize backing store write amplification.

Recently, our Database Reliability and Data Consistency teams escalated three high-severity anomalies:
- **Ticket #CACHE-601 (Read-Your-Own-Writes Violation):** Applications that write a key and immediately read it back receive stale data from disk whenever the in-memory key has been evicted from the LRU cache prior to a buffer flush.
- **Ticket #CACHE-602 (Dirty Key Eviction Data Loss):** Under heavy memory pressure, LRU cache eviction permanently drops pending writes from the write buffer without persisting them to disk, resulting in silent data corruption.
- **Ticket #CACHE-603 (TTL Expiration Bypassed):** Keys configured with short TTLs continue serving stale data after expiration because the cache hit handler returns the value without evaluating the expiration timestamp.

You are tasked with diagnosing the cache coherence defects across our storage tier, implementing an architecturally sound solution, verifying behavior deterministically using our test clock, and preparing to defend your architecture in your technical interview.

---

## 🚀 Running the Backend Service & Tests

This task is configured as a **Backend Service with a REST API** and unit tests. You can test your changes using either the interactive HTTP endpoints or the automated test suite.

### Option A: Interactive REST API Service
1. **Launch the Backend API Server:**
   ```bash
   python3 api.py
   ```
   *Runs on `http://localhost:8000` (FastAPI / Swagger docs at `/docs` if requirements installed, with built-in zero-dependency fallback).*

2. **Interact with the Endpoints:**
   - `GET /api/state`: Inspect cache entries, dirty write buffer, and persistent backing store.
   - `POST /api/cache`: Write a key with optional TTL (`{"key": "user_1", "value": "Alice", "ttl_seconds": 60}`).
   - `GET /api/cache/{key}`: Query a key and observe read-your-own-writes behavior.
   - `POST /api/flush`: Flush dirty buffer to disk.
   - `POST /api/clock/advance`: Advance deterministic virtual clock (`{"seconds": 65}`).

### Option B: Command-Line Test Suite
Run the test suite directly from the task root:
```bash
python3 -m unittest discover tests
```
Observe failures in:
- `test_bug_reproduction_ticket_cache_601_read_your_own_writes_buffer_bypass`
- `test_bug_reproduction_ticket_cache_602_dirty_key_eviction_data_loss`
- `test_bug_reproduction_ticket_cache_603_ttl_expiration_returns_none`

---

## Your Objectives

1. **Investigate Codebase:**
   - `src/models.py`: Domain dataclasses (`CacheEntry`, `CacheStats`).
   - `src/clock.py`: Time abstraction (`Clock`, `SystemClock`, `TestClock`).
   - `src/storage.py`: Backing store interface and in-memory storage mock.
   - `src/lru_cache.py`: LRU cache pool with eviction callbacks.
   - `src/cache_manager.py`: Cache orchestrator managing read prioritizations, write buffer staging, and flushing (**YOUR TASK IS HERE**).

2. **Analyze Root Causes:**
   - **Read Prioritization:** Why must reads inspect `_write_buffer` before falling back to the backing store?
   - **Eviction Safety:** What happens when `_handle_eviction` deletes a dirty entry from `_write_buffer`?
   - **TTL Enforcement:** What check is required before returning a cached entry?

3. **Implement the Fix:**
   - In `src/cache_manager.py`:
     - **Buffer Prioritization:** Check `self._write_buffer` first in `get(key)`. If a key is present in the dirty buffer, check its TTL and return its value immediately.
     - **Protect Dirty Writes:** In `_handle_eviction(evicted_entry)`, if the entry is dirty (`evicted_entry.is_dirty`), do NOT delete it from `_write_buffer`. Keep it in `_write_buffer` so it is safely flushed later.
     - **Enforce TTL Expiration:** In `get(key)`, if `entry.expires_at is not None and entry.expires_at <= now`, treat it as expired: remove it from `_cache` and return `None`.
     - In `put(...)`: Validate that `ttl_seconds` (if provided) is strictly positive (`ttl_seconds > 0`), raising `ValueError` otherwise.

4. **Expand Test Coverage:**
   - Add unit tests in `tests/test_cache_sync.py` covering:
     - Dirty key updates before flushing.
     - Non-positive TTL validation error handling.
     - Exact expiration boundary timing.
     - Idempotent subsequent flushes.

5. **Prepare for Technical Defense:**
   - Be prepared to discuss cache coherence models (write-through, write-back, write-around), cache stampedes, distributed lock invalidation, and memory reclamation during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only.
- Do not use `time.sleep()`. Use `TestClock` to advance time deterministically.
- Do not alter public method signatures of `WriteThroughCacheManager`.
- Demonstrate clean engineering judgment and data integrity protection.
