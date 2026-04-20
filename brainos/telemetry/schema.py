"""SQLite telemetry schema.

TelemetryDB manages a local SQLite database for event logging and analytics.
It tracks every query, ingestion, reflection, and publish event so that:
  - Users can reflect on their thinking patterns
  - System usage can be measured and optimized
  - Multi-session history is preserved

Schema:
  - events: Generic events (query, ingest, reflect, publish) with metadata
  - query_history: Query-specific records with result counts and scores

All writes use INSERT OR REPLACE to handle idempotency. The database lives
in .brainos/telemetry.db by default and is created automatically on first use.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class TelemetryDB:
    """SQLite database for telemetry and event logging."""

    def __init__(self, db_path: str | Path = "./.brainos/telemetry.db"):
        """Initialize telemetry database.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()

        # Events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                query TEXT,
                num_results INTEGER,
                tokens_used INTEGER,
                context_layers TEXT,
                metadata TEXT,
                UNIQUE(timestamp, event_type, query)
            )
            """
        )

        # Query history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                query TEXT NOT NULL,
                num_semantic_results INTEGER,
                num_graph_results INTEGER,
                top_result_score REAL,
                UNIQUE(timestamp, query)
            )
            """
        )

        self.conn.commit()

    def log_event(
        self,
        event_type: str,
        query: Optional[str] = None,
        num_results: Optional[int] = None,
        tokens_used: Optional[int] = None,
        context_layers: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an event.

        Args:
            event_type: Type of event (query, ingest, reflect, etc.)
            query: Query string if applicable
            num_results: Number of results returned
            tokens_used: Tokens consumed
            context_layers: Layers used (comma-separated)
            metadata: Additional JSON metadata
        """
        cursor = self.conn.cursor()
        metadata_str = str(metadata) if metadata else None

        cursor.execute(
            """
            INSERT OR REPLACE INTO events
            (event_type, query, num_results, tokens_used, context_layers, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_type, query, num_results, tokens_used, context_layers, metadata_str),
        )

        self.conn.commit()

    def log_query(
        self,
        query: str,
        num_semantic_results: int,
        num_graph_results: int,
        top_result_score: float = 0.0,
    ):
        """Log a query execution.

        Args:
            query: Query string
            num_semantic_results: Semantic results returned
            num_graph_results: Graph results returned
            top_result_score: Score of top result
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO query_history
            (query, num_semantic_results, num_graph_results, top_result_score)
            VALUES (?, ?, ?, ?)
            """,
            (query, num_semantic_results, num_graph_results, top_result_score),
        )

        self.conn.commit()

    def get_event_stats(self, event_type: str = None) -> Dict[str, Any]:
        """Get statistics for events.

        Args:
            event_type: Optional filter by event type

        Returns:
            Dictionary with stats
        """
        cursor = self.conn.cursor()

        if event_type:
            cursor.execute(
                "SELECT COUNT(*) as count, AVG(tokens_used) as avg_tokens FROM events WHERE event_type = ?",
                (event_type,),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count, AVG(tokens_used) as avg_tokens FROM events"
            )

        row = cursor.fetchone()
        return {"event_count": row["count"], "avg_tokens": row["avg_tokens"] or 0}

    def get_top_queries(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get top queries by frequency.

        Args:
            limit: Max results

        Returns:
            List of queries with counts
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT query, COUNT(*) as count, AVG(top_result_score) as avg_score
            FROM query_history
            GROUP BY query
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        self.conn.close()
