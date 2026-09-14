"""Immutable State Persistence & SQLite Audit Ledger.

Records append-only transition snapshots of every pipeline stage,
storing payloads, retrieved literature, draft artifacts, and verification audits.
"""

import sqlite3
import json
import os
from typing import Optional, List, Dict, Any
from src.schemas.pipeline_state import PipelineState


class StateStore:
    """Append-only snapshot store backed by SQLite."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._shared_conn = None
        if db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    topic TEXT NOT NULL,
                    risk_category TEXT NOT NULL,
                    audit_passed INTEGER NOT NULL,
                    rejection_reason TEXT,
                    state_json TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_idempotency_step 
                ON pipeline_snapshots(idempotency_key, step_name);
            """)
            conn.commit()

    def save_snapshot(
        self,
        execution_id: str,
        idempotency_key: str,
        step_name: str,
        state: PipelineState
    ) -> int:
        """Appends an immutable state snapshot."""
        state_data = state.model_dump_json()
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO pipeline_snapshots (
                    execution_id,
                    idempotency_key,
                    step_name,
                    topic,
                    risk_category,
                    audit_passed,
                    rejection_reason,
                    state_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id,
                idempotency_key,
                step_name,
                state.raw_topic,
                state.risk_category,
                1 if state.audit_passed else 0,
                state.rejection_reason,
                state_data
            ))
            conn.commit()
            return cursor.lastrowid

    def get_latest_checkpoint(self, idempotency_key: str, step_name: Optional[str] = None) -> Optional[PipelineState]:
        """Retrieves the latest verified checkpoint for idempotency resumption."""
        query = """
            SELECT state_json FROM pipeline_snapshots
            WHERE idempotency_key = ? AND audit_passed = 1
        """
        params = [idempotency_key]
        if step_name:
            query += " AND step_name = ?"
            params.append(step_name)
        query += " ORDER BY id DESC LIMIT 1"

        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            if row:
                data = json.loads(row["state_json"])
                return PipelineState.model_validate(data)
        return None

    def get_execution_history(self, execution_id: str) -> List[Dict[str, Any]]:
        """Returns ordered timeline of execution steps."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, step_name, created_at, audit_passed, rejection_reason
                FROM pipeline_snapshots
                WHERE execution_id = ?
                ORDER BY id ASC
            """, (execution_id,)).fetchall()
            return [dict(r) for r in rows]
