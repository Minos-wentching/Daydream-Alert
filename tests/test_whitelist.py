from app.core.models import ActiveWindowInfo
from app.core.whitelist import is_window_allowed


def test_allowed_when_no_rules():
    w = ActiveWindowInfo(process_name="chrome.exe", window_title="LeetCode")
    assert is_window_allowed(w, [], [])


def test_process_whitelist_case_insensitive():
    w = ActiveWindowInfo(process_name="CHROME.EXE", window_title="X")
    assert is_window_allowed(w, ["chrome.exe"], [])
    assert not is_window_allowed(w, ["code.exe"], [])


def test_title_keywords_match():
    w = ActiveWindowInfo(process_name="chrome.exe", window_title="LeetCode - Problem")
    assert is_window_allowed(w, [], ["LeetCode"])
    assert not is_window_allowed(w, [], ["Notion"])


def test_both_rules_must_pass_when_both_provided():
    w = ActiveWindowInfo(process_name="chrome.exe", window_title="LeetCode - Problem")
    assert is_window_allowed(w, ["chrome.exe"], ["LeetCode"])
    assert not is_window_allowed(w, ["chrome.exe"], ["Notion"])

