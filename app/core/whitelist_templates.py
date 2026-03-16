from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WhitelistTemplate:
    name: str
    allowed_process_names: list[str]
    allowed_title_keywords: list[str]


class WhitelistTemplateStore:
    def __init__(self, path: Path | None = None):
        self._path = path or (Path('data') / 'whitelist_templates.json')

    def list_templates(self) -> list[WhitelistTemplate]:
        return sorted(self._load_all(), key=lambda t: t.name)

    def has_template(self, name: str) -> bool:
        name = name.strip()
        if not name:
            return False
        return any(t.name == name for t in self._load_all())

    def get_template(self, name: str) -> WhitelistTemplate | None:
        name = name.strip()
        if not name:
            return None
        for t in self._load_all():
            if t.name == name:
                return t
        return None

    def upsert_template(
        self, *, name: str, allowed_process_names: list[str], allowed_title_keywords: list[str]
    ) -> None:
        name = self._validate_name(name)
        templates = self._load_all()

        normalized = WhitelistTemplate(
            name=name,
            allowed_process_names=sorted({p.strip().lower() for p in allowed_process_names if p.strip()}),
            allowed_title_keywords=sorted({k.strip() for k in allowed_title_keywords if k.strip()}),
        )

        out: list[WhitelistTemplate] = []
        replaced = False
        for t in templates:
            if t.name == name:
                out.append(normalized)
                replaced = True
            else:
                out.append(t)
        if not replaced:
            out.append(normalized)

        self._save_all(out)

    def delete_template(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        templates = [t for t in self._load_all() if t.name != name]
        self._save_all(templates)

    def _validate_name(self, name: str) -> str:
        name = (name or '').strip()
        if not name:
            raise ValueError('template name is required')
        if len(name) > 40:
            raise ValueError('template name too long (max 40 chars)')
        if any(ch in name for ch in '\r\n\t'):
            raise ValueError('template name contains invalid whitespace')
        return name

    def _load_all(self) -> list[WhitelistTemplate]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding='utf-8'))
        except Exception:
            return []

        items = raw.get('templates', []) if isinstance(raw, dict) else []
        out: list[WhitelistTemplate] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get('name', '')).strip()
            if not name:
                continue
            procs = item.get('allowed_process_names', [])
            keys = item.get('allowed_title_keywords', [])
            if not isinstance(procs, list) or not isinstance(keys, list):
                continue
            out.append(
                WhitelistTemplate(
                    name=name,
                    allowed_process_names=[str(p) for p in procs if str(p).strip()],
                    allowed_title_keywords=[str(k) for k in keys if str(k).strip()],
                )
            )
        return out

    def _save_all(self, templates: list[WhitelistTemplate]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'version': 1,
            'templates': [
                {
                    'name': t.name,
                    'allowed_process_names': t.allowed_process_names,
                    'allowed_title_keywords': t.allowed_title_keywords,
                }
                for t in sorted(templates, key=lambda t: t.name)
            ],
        }
        tmp = self._path.with_suffix(self._path.suffix + '.tmp')
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(self._path)
