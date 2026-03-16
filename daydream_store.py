from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.models import ActiveWindowInfo, FocusState, StateUpdate, TaskConfig


@dataclass
class _Segment:
    state: FocusState
    start_at: datetime
    end_at: Optional[datetime]
    reasons: tuple[str, ...]
    active_window: Optional[ActiveWindowInfo]


class SqliteSessionRecorder:
    """
    Writes session + segments into a local SQLite DB.

    Privacy: stores only timestamps, state, reasons, and active window metadata.
    """

    def __init__(self, db_path: Path, config: TaskConfig, started_at: datetime):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._ensure_schema()

        config_json = json.dumps(config.model_dump(mode="json"), ensure_ascii=False)
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO sessions(task_name, started_at, ended_at, config_json)
            VALUES (?, ?, NULL, ?)
            """,
            (config.task_name, started_at.isoformat(), config_json),
        )
        self._session_id = int(cur.lastrowid)
        self._conn.commit()

        self._current: Optional[_Segment] = None

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_name TEXT NOT NULL,
              started_at TEXT NOT NULL,
              ended_at TEXT,
              config_json TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS segments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              state TEXT NOT NULL,
              start_at TEXT NOT NULL,
              end_at TEXT NOT NULL,
              reasons TEXT,
              process_name TEXT,
              window_title TEXT,
              pid INTEGER,
              FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_session ON segments(session_id)")
        self._conn.commit()

    def on_update(self, update: StateUpdate) -> None:
        if self._current is None:
            self._current = _Segment(
                state=update.observed_state,
                start_at=update.now,
                end_at=None,
                reasons=update.reasons,
                active_window=update.active_window,
            )
            return

        if update.observed_state == self._current.state:
            return

        self._write_segment(
            _Segment(
                state=self._current.state,
                start_at=self._current.start_at,
                end_at=update.now,
                reasons=self._current.reasons,
                active_window=self._current.active_window,
            )
        )
        self._current = _Segment(
            state=update.observed_state,
            start_at=update.now,
            end_at=None,
            reasons=update.reasons,
            active_window=update.active_window,
        )

    def finalize(self, ended_at: datetime) -> None:
        if self._current is not None:
            self._write_segment(
                _Segment(
                    state=self._current.state,
                    start_at=self._current.start_at,
                    end_at=ended_at,
                    reasons=self._current.reasons,
                    active_window=self._current.active_window,
                )
            )
            self._current = None

        self._conn.execute(
            "UPDATE sessions SET ended_at=? WHERE id=?",
            (ended_at.isoformat(), self._session_id),
        )
        self._conn.commit()
        self._conn.close()

    def _write_segment(self, segment: _Segment) -> None:
        if segment.end_at is None:
            return

        process_name = segment.active_window.process_name if segment.active_window else None
        window_title = segment.active_window.window_title if segment.active_window else None
        pid = segment.active_window.pid if segment.active_window else None
        reasons = "|".join(segment.reasons) if segment.reasons else ""

        self._conn.execute(
            """
            INSERT INTO segments(session_id, state, start_at, end_at, reasons, process_name, window_title, pid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._session_id,
                segment.state.value,
                segment.start_at.isoformat(),
                segment.end_at.isoformat(),
                reasons,
                process_name,
                window_title,
                pid,
            ),
        )
        self._conn.commit()

