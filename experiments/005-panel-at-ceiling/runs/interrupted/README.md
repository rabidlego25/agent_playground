Partial traces from interrupted runs. Kept rather than deleted, so a phase that was
re-run is visible in the record instead of silently replaced.

- `005_delib_qwen2.5.partial-30.jsonl` — 2026-09-01. The chained five-phase run was killed
  30/195 into the qwen2.5 deliberation phase. `TraceWriter` is append-only, so resuming
  into the same file would have duplicated those 30 tasks. The phase was restarted from
  zero; this file is the discarded prefix, not part of any reported arm.
