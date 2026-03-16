from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.models import ActiveWindowInfo, FocusState, StateUpdate


@dataclass
class _Segment:
    state: FocusState
    start_at: datetime
    end_at: Optional[datetime] = None
    reasons: tuple[str, ...] = ()
    active_window: Optional[ActiveWindowInfo] = None


class SessionLogger:
    def __init__(self, task_name: str, started_at: datetime, base_dir: Path | None = None):
        self._task_name = task_name
        self._started_at = started_at
        self._base_dir = base_dir or Path("logs")
        self._segments: List[_Segment] = []
        self._current: Optional[_Segment] = None

    def on_update(self, update: StateUpdate) -> None:
        if self._current is None:
            self._current = _Segment(
                state=update.observed_state,
                start_at=update.now,
                reasons=update.reasons,
                active_window=update.active_window,
            )
            return

        if update.observed_state == self._current.state:
            return

        self._current.end_at = update.now
        self._segments.append(self._current)
        self._current = _Segment(
            state=update.observed_state,
            start_at=update.now,
            reasons=update.reasons,
            active_window=update.active_window,
        )

    def finalize(self, ended_at: datetime) -> None:
        if self._current is not None and self._current.end_at is None:
            self._current.end_at = ended_at
            self._segments.append(self._current)
            self._current = None

    def export_json(self) -> Path:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in self._task_name)[:60] or "task"
        stamp = self._started_at.strftime("%Y%m%d_%H%M%S")
        path = self._base_dir / f"{stamp}_{safe_name}.json"

        payload: Dict[str, Any] = {
            "task_name": self._task_name,
            "started_at": self._started_at.isoformat(),
            "segments": [
                {
                    "state": s.state.value,
                    "start_at": s.start_at.isoformat(),
                    "end_at": (s.end_at.isoformat() if s.end_at else None),
                    "reasons": list(s.reasons),
                    "active_window": (s.active_window.model_dump() if s.active_window else None),
                }
                for s in self._segments
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def export_csv(self) -> Path:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in self._task_name)[:60] or "task"
        stamp = self._started_at.strftime("%Y%m%d_%H%M%S")
        path = self._base_dir / f"{stamp}_{safe_name}.csv"

        lines = ["state,start_at,end_at,reasons,process_name,window_title,pid"]
        for s in self._segments:
            process_name = s.active_window.process_name if s.active_window else ""
            window_title = (s.active_window.window_title if s.active_window else "").replace('"', '""')
            pid = str(s.active_window.pid) if (s.active_window and s.active_window.pid is not None) else ""
            reasons = "|".join(s.reasons).replace('"', '""')
            lines.append(
                f'{s.state.value},{s.start_at.isoformat()},{(s.end_at.isoformat() if s.end_at else "")},'
                f'"{reasons}","{process_name}","{window_title}",{pid}'
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

