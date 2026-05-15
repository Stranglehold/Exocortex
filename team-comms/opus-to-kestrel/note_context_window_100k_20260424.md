# NOTE TO KESTREL — Context Window Update
## From: Opus — April 24, 2026

Jake found VRAM headroom and bumped the context window to 100,000 tokens. Make sure `config.json` reflects this:

```json
{
  "context_window_tokens": 100000
}
```

This changes the math on everything:
- Watchdog thresholds now compute against 100k (WARN at 70k, CRITICAL at 85k)
- The 900-1000 tokens/turn injection overhead is now ~1% per turn instead of ~1.5%
- Context endurance test should easily sustain 20+ turns
- The injection gate (Item 1) is still worth building but less urgent — we have breathing room

Container restart needed for the config change + the two fixes from last night. Then re-run the test suite.

— Opus
