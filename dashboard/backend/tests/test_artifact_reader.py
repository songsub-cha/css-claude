"""T4.7 RED scaffold — artifact_reader tests (cache-first from api-specialist spec)."""
import pytest
from pathlib import Path
from backend.services.artifact_reader import resolve_artifact_path, ArtifactNotFound, ArtifactForbidden


def test_resolve_spec(tmp_path):
    spec = tmp_path / "docs/specs/x.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("hi")
    session = {
        "slug": "feat-x",
        "phases": {"interview": {"artifact": "docs/specs/x.md"}},
        "repo_root": str(tmp_path),
    }
    assert resolve_artifact_path(session, "spec") == spec.resolve()


def test_path_traversal_blocked(tmp_path):
    session = {
        "slug": "feat-x",
        "phases": {"interview": {"artifact": "../../../../etc/passwd"}},
        "repo_root": str(tmp_path),
    }
    with pytest.raises(ArtifactForbidden):
        resolve_artifact_path(session, "spec")


def test_unknown_name_rejected(tmp_path):
    with pytest.raises(ArtifactNotFound):
        resolve_artifact_path({"slug": "x", "phases": {}, "repo_root": str(tmp_path)}, "evil-name")
