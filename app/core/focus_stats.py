from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SessionStats:
    session_id: int
    task_name: str
    started_at: datetime
    ended_at: datetime
    work_s: float
    distracted_s: float
    rest_s: float

    @property
    def total_s(self) -> float:
        return self.work_s + self.distracted_s + self.rest_s


@dataclass(frozen=True)
class PeriodStats:
    start_at: datetime
    end_at: datetime
    sessions: list[SessionStats]
    top_distracted_processes: list[tuple[str, float]]

    @property
    def work_s(self) -> float:
        return sum(s.work_s for s in self.sessions)

    @property
    def distracted_s(self) -> float:
        return sum(s.distracted_s for s in self.sessions)

    @property
    def rest_s(self) -> float:
        return sum(s.rest_s for s in self.sessions)

    @property
    def total_s(self) -> float:
        return self.work_s + self.distracted_s + self.rest_s


def _parse_dt(value: str) -> datetime:
    # Stored as ISO-8601 strings (usually timezone-aware).
    return datetime.fromisoformat(value)


def _overlap_seconds(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if end <= start:
        return 0.0
    return (end - start).total_seconds()


def load_period_stats(db_path: Path, start_at: datetime, end_at: datetime) -> PeriodStats:
    if end_at <= start_at:
        raise ValueError('end_at must be after start_at')

    if not db_path.exists():
        return PeriodStats(start_at=start_at, end_at=end_at, sessions=[], top_distracted_processes=[])

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT
              s.id,
              s.task_name,
              s.started_at,
              s.ended_at,
              g.state,
              g.start_at,
              g.end_at,
              COALESCE(g.process_name, '')
            FROM segments g
            JOIN sessions s ON s.id = g.session_id
            WHERE s.ended_at IS NOT NULL
              AND g.start_at < ?
              AND g.end_at > ?
            ORDER BY s.id ASC, g.start_at ASC
            ''',
            (end_at.isoformat(), start_at.isoformat()),
        )

        per_session: dict[int, dict] = {}
        distracted_by_process: dict[str, float] = {}

        for (
            session_id,
            task_name,
            session_started_at,
            session_ended_at,
            state,
            seg_start_at,
            seg_end_at,
            process_name,
        ) in cur.fetchall():
            try:
                seg_start = _parse_dt(seg_start_at)
                seg_end = _parse_dt(seg_end_at)
            except Exception:
                continue

            dur_s = _overlap_seconds(seg_start, seg_end, start_at, end_at)
            if dur_s <= 0:
                continue

            sid = int(session_id)
            info = per_session.get(sid)
            if info is None:
                try:
                    info = {
                        'session_id': sid,
                        'task_name': str(task_name or ''),
                        'started_at': _parse_dt(session_started_at),
                        'ended_at': _parse_dt(session_ended_at),
                        'work_s': 0.0,
                        'distracted_s': 0.0,
                        'rest_s': 0.0,
                    }
                except Exception:
                    continue
                per_session[sid] = info

            if state == 'work':
                info['work_s'] += dur_s
            elif state == 'distracted':
                info['distracted_s'] += dur_s
                key = (process_name or '').strip() or '(unknown)'
                distracted_by_process[key] = distracted_by_process.get(key, 0.0) + dur_s
            elif state == 'rest':
                info['rest_s'] += dur_s

        sessions = [
            SessionStats(
                session_id=info['session_id'],
                task_name=info['task_name'],
                started_at=info['started_at'],
                ended_at=info['ended_at'],
                work_s=info['work_s'],
                distracted_s=info['distracted_s'],
                rest_s=info['rest_s'],
            )
            for info in per_session.values()
        ]
        sessions.sort(key=lambda s: s.started_at)

        top_processes = sorted(distracted_by_process.items(), key=lambda kv: kv[1], reverse=True)[:12]

        return PeriodStats(
            start_at=start_at,
            end_at=end_at,
            sessions=sessions,
            top_distracted_processes=top_processes,
        )
    finally:
        conn.close()
