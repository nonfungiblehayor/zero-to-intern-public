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

You are tasked with diagnosing the cache coherence defects across our storage tier, implementing an architecturally sound solution, verifying behavior deterministically using our test clock, and completing our engineering post-mortem.

---

## Your Objectives

1. **Investigate Codebase:**
   - `src/models.py`: Domain dataclasses (`CacheEntry`, `CacheStats`).
   - `src/clock.py`: Time abstraction (`Clock`, `SystemClock`, `TestClock`).
   - `src/storage.py`: Backing store interface and in-memory mock.
   - `src/lru_cache.py`: LRU cache pool with eviction callbacks.
   - `src/cache_manager.py`: Cache orchestrator managing read prioritizations, write buffer staging, and flushing.
2. **Reproduce the Defect:**
   ```bash
   python3 -m unittest discover tests
   ```
   Observe the failures in:
   - `test_bug_reproduction_ticket_cache_601_read_your_own_writes_buffer_bypass`
   - `test_bug_reproduction_ticket_cache_602_dirty_key_eviction_data_loss`
   - `test_bug_reproduction_ticket_cache_603_ttl_expiration_returns_none`
3. **Analyze Root Causes:**
   - **Read Prioritization:** Why must reads inspect `_write_buffer` before falling back to the backing store?
   - **Eviction Safety:** What happens when `_handle_eviction` deletes a dirty entry from `_write_buffer`?
   - **TTL Enforcement:** What check is required before returning a cached entry?
4. **Implement the Fix:**
   - In `src/cache_manager.py`:
     - **Buffer Prioritization:** Check `self._write_buffer` first in `get(key)`. If a key is present in the dirty buffer, check its TTL and return its value immediately.
     - **Protect Dirty Writes:** In `_handle_eviction(evicted_entry)`, if the entry is dirty (`evicted_entry.is_dirty`), do NOT delete it from `_write_buffer`. Keep it in `_write_buffer` so it is safely flushed later.
     - **Enforce TTL Expiration:** In `get(key)`, if `entry.expires_at is not None and entry.expires_at <= now`, treat it as expired: remove it from `_cache` and return `None`.
5. **Add Unit Tests:**
   - Expand `tests/test_cache_sync.py` to cover dirty key updates, zero-capacity edge cases, and clock boundary transitions using `TestClock`.
6. **Complete Documentation:**
   - Fill out all sections in [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-3-advanced/task-2-cache-sync/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Python 3 Standard Library only. Do not install external libraries.
- Do not use `time.sleep()`. Use `TestClock` to advance time deterministically.
- Do not alter public method signatures of `WriteThroughCacheManager`.
- Document all consistency and eviction trade-offs in `CANDIDATE_SUBMISSION.md`.
