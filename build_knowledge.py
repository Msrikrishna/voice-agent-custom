"""Build a tiny knowledge index from `knowledge_sources/*.md`.

This is a stripped-down version of a real RAG pipeline — just enough so your
agent can search local notes for facts at call time. For the workshop you'll
likely just edit `knowledge_sources/example.md` (or have Claude Code generate
new files) and re-run this.

Output:
    knowledge/index.json   — list of {id, title, summary, body}
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = AGENT_DIR / "knowledge"
KNOWLEDGE_SOURCES_DIR = AGENT_DIR / "knowledge_sources"

_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def _summary(body: str, limit: int = 240) -> str:
    text = body.strip()
    for chunk in re.split(r"\n\s*\n", text):
        chunk = chunk.strip()
        if not chunk or chunk.startswith("#") or chunk.startswith("```"):
            continue
        return re.sub(r"\s+", " ", chunk)[:limit]
    return re.sub(r"\s+", " ", text)[:limit]


def main() -> int:
    if KNOWLEDGE_DIR.exists():
        shutil.rmtree(KNOWLEDGE_DIR)
    KNOWLEDGE_DIR.mkdir(parents=True)

    if not KNOWLEDGE_SOURCES_DIR.is_dir():
        print(f"[error] {KNOWLEDGE_SOURCES_DIR} does not exist")
        return 1

    entries = []
    for src in sorted(KNOWLEDGE_SOURCES_DIR.glob("*.md")):
        body = src.read_text(encoding="utf-8")
        title_match = _HEADING_RE.search(body)
        title = title_match.group(1) if title_match else src.stem.replace("-", " ").title()
        slug = src.stem
        entry = {
            "id": slug,
            "title": title,
            "summary": _summary(body),
            "body": body,
        }
        (KNOWLEDGE_DIR / f"{slug}.md").write_text(body, encoding="utf-8")
        entries.append(entry)

    (KNOWLEDGE_DIR / "index.json").write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[ok] wrote {len(entries)} pages to {KNOWLEDGE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
