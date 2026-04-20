"""Telemetry and event logging.

Records system usage, queries, and agent events to a local SQLite database.
Telemetry enables:
  - Reflection: Analyze thinking patterns and query frequency
  - Analytics: Track token usage, event counts, and trends
  - Debugging: Inspect what was queried and when

All data stays local (privacy-first). The schema is simple but extensible:
  - events table: Generic event log (type, query, results, tokens, metadata)
  - query_history table: Detailed query execution records
"""
