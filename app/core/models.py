from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable, List, Optional

from pydantic import BaseModel, Field


class FocusState(str, Enum):
    WORK = "work"
    DISTRACTED = "distracted"
    REST = "rest"


class ActiveWindowInfo(BaseModel):
    process_name: str = ""
    window_title: str = ""
    pid: Optional[int] = None


class TaskConfig(BaseModel):
    task_name: str = Field(min_length=1)
    start_at: datetime
    end_at: datetime

    distract_alarm_after_s: int = 3 * 60
    release_alarm_after_work_s: int = 2 * 60
    exit_button_after_s: int = 10 * 60

    allowed_process_names: List[str] = Field(default_factory=list)
    allowed_title_keywords: List[str] = Field(default_factory=list)

    sample_interval_ms: int = 1000
    enable_camera: bool = True
    enable_yolo_phone: bool = True
    enable_face_pose: bool = True

    def normalized(self) -> "TaskConfig":
        normalized_processes = sorted(
            {p.strip().lower() for p in self.allowed_process_names if p.strip()}
        )
        normalized_keywords = sorted({k.strip() for k in self.allowed_title_keywords if k.strip()})
        return self.model_copy(
            update={
                "allowed_process_names": normalized_processes,
                "allowed_title_keywords": normalized_keywords,
            }
        )


@dataclass(frozen=True)
class Observation:
    observed_state: FocusState
    reasons: tuple[str, ...] = ()
    active_window: Optional[ActiveWindowInfo] = None


@dataclass(frozen=True)
class StateUpdate:
    now: datetime
    observed_state: FocusState
    alarm_on: bool
    distracted_accumulated_s: float
    work_streak_s: float
    reasons: tuple[str, ...]
    active_window: Optional[ActiveWindowInfo]


def normalize_lines(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        if not value:
            continue
        for part in value.replace(",", "\n").splitlines():
            part = part.strip()
            if part:
                out.append(part)
    return out

