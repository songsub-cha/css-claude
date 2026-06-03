"""Install CSS Codex artifacts into ~/.codex (transform + copy).

Single source of truth = the repo's commands/ and agents/. This module writes
only under `codex_home`, so the Claude Code install is never affected.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from codex_install.transform import build_index, transform_agent, transform_command


def install(source_root, codex_home, force=False):
    """Transform repo CSS sources into Codex artifacts under `codex_home`.

    Returns {"commands": int, "agents": int, "config_written": bool}.
    Idempotent: re-running regenerates identical files; config.json is only
    written when missing or force=True (matching the Claude installer).
    """
    source_root = Path(source_root)
    codex_home = Path(codex_home)
    prompts_dir = codex_home / "prompts"
    css_dir = codex_home / "css"
    agents_dir = css_dir / "agents"
    for d in (prompts_dir, agents_dir):
        d.mkdir(parents=True, exist_ok=True)

    cmd_count = 0
    for md in sorted((source_root / "commands").glob("*.md")):
        out = transform_command(md.read_text(encoding="utf-8"))
        (prompts_dir / f"css-{md.stem}.md").write_text(out, encoding="utf-8")
        cmd_count += 1

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

    return {"commands": cmd_count, "agents": len(index), "config_written": config_written}
