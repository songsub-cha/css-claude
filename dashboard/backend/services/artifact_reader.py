"""T4.7 — Artifact path resolution with whitelist and traversal guard."""
from pathlib import Path
from typing import Optional

WHITELIST = {"spec", "plan", "exec-log", "verify", "code-review", "security-review", "docs"}


class ArtifactNotFound(Exception):
    pass


class ArtifactForbidden(Exception):
    pass


def _is_rich_spec_name(name: str) -> bool:
    return name.startswith("rich-spec-") and len(name) <= 64


def resolve_artifact_path(session: dict, name: str) -> Path:
    """Resolve artifact name to an absolute path inside repo_root.

    Raises ArtifactNotFound for unknown/missing artifacts.
    Raises ArtifactForbidden for path traversal attempts.
    """
    if name not in WHITELIST and not _is_rich_spec_name(name):
        raise ArtifactNotFound(name)

    repo_root = Path(session.get("repo_root", "")).resolve()
    if not repo_root.exists():
        raise ArtifactNotFound("repo_root missing")

    candidate: Optional[Path] = None
    phases = session.get("phases", {})
    slug = session.get("slug", "")

    if name == "spec":
        rel = phases.get("interview", {}).get("artifact") if isinstance(phases.get("interview"), dict) else None
        if rel:
            candidate = repo_root / rel
    elif name == "plan":
        rel = phases.get("plan", {}).get("artifact") if isinstance(phases.get("plan"), dict) else None
        if rel:
            candidate = repo_root / rel
    elif name == "exec-log":
        d = repo_root / ".claude/css/executions"
        if d.exists():
            files = sorted(d.glob(f"exec-log-{slug}-*.md"))
            candidate = files[-1] if files else None
    elif name == "verify":
        d = repo_root / ".claude/css/verifies"
        if d.exists():
            files = sorted(d.glob(f"verify-{slug}-*.md"))
            candidate = files[-1] if files else None
    elif name in ("code-review", "security-review"):
        # derived from verify report — implemented in T4.7b
        raise ArtifactNotFound(name)
    elif _is_rich_spec_name(name):
        task_id = name[len("rich-spec-"):]
        d = repo_root / ".claude/css/plans"
        if d.exists():
            files = sorted(d.glob(f"{task_id}-spec-{slug}-*.md"))
            candidate = files[-1] if files else None
    elif name == "docs":
        candidate = repo_root / "docs" / slug / "README.md"

    if candidate is None:
        raise ArtifactNotFound(name)

    # Resolve to absolute and check traversal
    resolved = candidate.resolve()
    repo_root_str = str(repo_root)
    resolved_str = str(resolved)

    # Must be inside repo_root (allow exact match or subpath)
    if resolved_str != repo_root_str and not resolved_str.startswith(repo_root_str + "/" ) and not resolved_str.startswith(repo_root_str + "\\"):
        raise ArtifactForbidden(f"{resolved} outside {repo_root}")

    if not resolved.exists() or not resolved.is_file():
        raise ArtifactNotFound(str(resolved))

    return resolved
