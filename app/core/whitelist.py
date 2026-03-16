from __future__ import annotations

from app.core.models import ActiveWindowInfo


def is_window_allowed(
    active_window: ActiveWindowInfo | None,
    allowed_process_names: list[str],
    allowed_title_keywords: list[str],
) -> bool:
    if active_window is None:
        return True

    process_name = (active_window.process_name or "").strip().lower()
    window_title = (active_window.window_title or "").strip()

    process_ok = True
    if allowed_process_names:
        process_ok = process_name in {p.strip().lower() for p in allowed_process_names if p.strip()}

    title_ok = True
    if allowed_title_keywords:
        title_ok = any(k in window_title for k in allowed_title_keywords if k)

    return process_ok and title_ok

