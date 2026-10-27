# Candidate Brief: StreamCompactor Storage Engine (BH-L3-005)

## Welcome to the StreamCompactor Engineering Team

Welcome to the Streaming Storage Platform team! Our `StreamCompactor` engine powers partitioned, append-only event logs, providing changelog compaction and index management for real-time stream processing.

Recently, customer-facing teams reported ghost record resurrections and consumer group offset errors after nightly log compaction passes. Three critical tickets have been assigned to your sprint.

---

## Assigned Tickets

### Ticket #STREAM-901: Tombstone Premature Purge Resurrects Records
- **Severity:** Critical
- **Reporter:** Customer Data Platform Team
- **Description:** When a user is deleted from a partitioned changelog stream, a tombstone record (`value=None`) is appended to a new segment. However, during incremental compaction, the compactor discards the tombstone from the compacted segment output. When downstream consumers replay the stream across the older uncompacted segment and the new compacted segment, the old user record is re-read and restored to the database!
- **Expected Behavior:** A tombstone must be retained in the compacted segment output as long as any older uncompacted segment contains that key. It may only be purged once all older segments containing that key have been fully merged and superseded.
- **Observed Behavior:** The compactor drops tombstones unconditionally during compaction, causing deleted records to resurrect.

### Ticket #STREAM-902: Partition Watermark Regression via Inverted Reduction
- **Severity:** High
- **Reporter:** Stream Analytics Infrastructure
- **Description:** Multiple consumer groups read from the same partition at different speeds. Consumer A is up-to-date at offset 500, but Consumer B is lagging at offset 50. The compactor calculates the safe compaction watermark using `max(consumer_watermarks)` (= 500), compacting away events between offset 50 and 500. When Consumer B resumes processing, its requested offsets no longer exist.
- **Expected Behavior:** The safe compaction watermark must be the minimum consumed offset across all registered consumers: `min(consumer_watermarks)`. Compaction must never proceed past the slowest active consumer.
- **Observed Behavior:** The compactor uses `max()`, allowing compaction to destroy unread data for lagging consumers.

### Ticket #STREAM-903: Sparse Index Offset Corruption During Compaction
- **Severity:** High
- **Reporter:** Real-Time Key Lookup Service
- **Description:** After a segment is compacted from 100 records down to 10 records, point lookups via `segment.get(key)` immediately fail with `IndexError: Index corrupted: position ... out of range`.
- **Expected Behavior:** When records are placed into the new compacted segment array at positions `0, 1, ..., N-1`, the internal index (`segment.index[key]`) must store the new position `new_pos`.
- **Observed Behavior:** The compactor assigns `segment.index[key] = rec.offset` (the old offset from the original uncompacted segment), which exceeds the length of the compacted records array.

---

## Instructions

1. Explore the codebase under `src/`:
   - `models.py`: Record definitions and segment metadata.
   - `segment.py`: `LogSegment` array storage and index lookup.
   - `stream_reader.py`: `PartitionStreamReader` log replay state.
   - `compactor.py`: `StreamCompactor` compaction and watermark engine.
2. Run the test suite:
   ```bash
   python3 -m unittest discover tests
   ```
   Notice that the 3 reproduction tests fail.
3. Fix the defects in `src/compactor.py`.
4. Verify all tests pass cleanly.
5. Author regression tests covering edge cases (multi-segment merges, self-contained tombstone purges, repeated compaction).
6. Fill in your technical explanation and storage mechanics analysis in `CANDIDATE_SUBMISSION.md`.
