"""Install CSS Codex artifacts (transform + copy).

Single source of truth = the repo's commands/ and agents/. This module writes
only under Codex user artifact locations, so the Claude Code install is never
affected.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from codex_install.transform import (
    build_index,
    transform_agent,
    transform_command_to_skill,
)


def install(source_root, codex_home, force=False, skills_home=None):
    """Transform repo CSS sources into Codex artifacts.

    Runtime data is written under `codex_home/css`; skills are written under
    `skills_home` (default: ~/.agents/skills).

    Returns {"skills": int, "agents": int, "config_written": bool}.
    Idempotent: re-running regenerates identical files; config.json is only
    written when missing or force=True (matching the Claude installer).
    """
    source_root = Path(source_root)
    codex_home = Path(codex_home)
    skills_home = Path(skills_home) if skills_home else Path.home() / ".agents" / "skills"
    css_dir = codex_home / "css"
    agents_dir = css_dir / "agents"
    for d in (skills_home, agents_dir):
        d.mkdir(parents=True, exist_ok=True)

    skill_count = 0
    for md in sorted((source_root / "commands").glob("*.md")):
        skill_name = f"css-{md.stem}"
        out = transform_command_to_skill(md.read_text(encoding="utf-8"), skill_name)
        skill_dir = skills_home / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(out, encoding="utf-8")
        skill_count += 1

    index = {}
    for md in sorted((source_root / "agents").glob("*.md")):
        name, body = transform_agent(md.read_text(encoding="utf-8"))
        (agents_dir / md.name).write_text(body, encoding="utf-8")
        index[name] = f"agents/{md.name}"
    (agents_dir / "index.json").write_text(
        json.dumps(build_index(index), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    shutil.copyfile(source_root / "codex" / "RUNTIME.md", css_dir / "RUNTIME.md")

    dst_config = css_dir / "config.json"
    config_written = False
    if force or not dst_config.exists():
        shutil.copyfile(source_root / "config" / "default-config.json", dst_config)
        config_written = True

    return {"skills": skill_count, "agents": len(index), "config_written": config_written}
