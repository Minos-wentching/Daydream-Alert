from datetime import datetime, timedelta, timezone

from app.core.focus_stats import load_period_stats


def test_load_period_stats_overlaps(tmp_path):
    import sqlite3

    db = tmp_path / 'daydream_focus.sqlite3'
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            '''
            CREATE TABLE sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_name TEXT NOT NULL,
              started_at TEXT NOT NULL,
              ended_at TEXT,
              config_json TEXT
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE segments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              state TEXT NOT NULL,
              start_at TEXT NOT NULL,
              end_at TEXT NOT NULL,
              reasons TEXT,
              process_name TEXT,
              window_title TEXT,
              pid INTEGER
            )
            '''
        )

        base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        conn.execute(
            'INSERT INTO sessions(id, task_name, started_at, ended_at, config_json) VALUES (1, ?, ?, ?, ?)',
            (
                't1',
                base.isoformat(),
                (base + timedelta(seconds=120)).isoformat(),
                '{}',
            ),
        )

        conn.executemany(
            'INSERT INTO segments(session_id, state, start_at, end_at, reasons, process_name, window_title, pid) VALUES (?,?,?,?,?,?,?,?)',
            [
                (1, 'work', base.isoformat(), (base + timedelta(seconds=60)).isoformat(), '', 'code.exe', '', None),
                (
                    1,
                    'distracted',
                    (base + timedelta(seconds=60)).isoformat(),
                    (base + timedelta(seconds=90)).isoformat(),
                    '',
                    'chrome.exe',
                    '',
                    None,
                ),
                (1, 'rest', (base + timedelta(seconds=90)).isoformat(), (base + timedelta(seconds=120)).isoformat(), '', '', '', None),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    # Overlap only [30, 100)
    start = base + timedelta(seconds=30)
    end = base + timedelta(seconds=100)

    stats = load_period_stats(db, start_at=start, end_at=end)
    assert len(stats.sessions) == 1
    s = stats.sessions[0]
    assert s.work_s == 30
    assert s.distracted_s == 30
    assert s.rest_s == 10

    assert stats.work_s == 30
    assert stats.distracted_s == 30
    assert stats.rest_s == 10

    assert stats.top_distracted_processes[0][0] == 'chrome.exe'
    assert stats.top_distracted_processes[0][1] == 30
