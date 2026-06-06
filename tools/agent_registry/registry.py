"""Parse CSS agent frontmatter, the executor Domain_Dispatch_Table, and the
README specialist tables; report any drift between them.

Source of truth is structural: a *domain specialist* is any `agents/*.md` whose
frontmatter `css_stages` contains BOTH ``review`` and ``execute`` (process
agents like the executor/reviewer/debugger never do). The executor dispatch
table must list exactly that set, and both READMEs must document at least that
set (review-only advisory agents such as ``css-architect`` may also appear).
"""
from __future__ import annotations

import re
from pathlib import Path

_DOMAIN_STAGES = {"review", "execute"}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_NAME_RE = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
_MODEL_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)
_STAGES_RE = re.compile(r"^css_stages:\s*\[([^\]]*)\]\s*$", re.MULTILINE)
_CSS_NAME = re.compile(r"css-[a-z0-9-]+")
_DISPATCH_SECTION = re.compile(
    r"<Domain_Dispatch_Table>(.*?)</Domain_Dispatch_Table>", re.DOTALL)
# A README specialist row: the FIRST table cell is a (optionally backticked)
# css-* name. This deliberately excludes the pipeline-stage table (first cell is
# ①/②/...) and any Mermaid nodes (lines that do not start with `|`).
_README_ROW = re.compile(r"^\|\s*`?(css-[a-z0-9-]+)`?\s*\|", re.MULTILINE)


def parse_agent_files(agents_dir) -> dict[str, dict]:
    """Return ``{name: {model, css_stages, path}}`` for every agents/*.md."""
    out: dict[str, dict] = {}
    for md in sorted(Path(agents_dir).glob("*.md")):
        fm = _FRONTMATTER_RE.match(md.read_text(encoding="utf-8"))
        if not fm:
            continue
        block = fm.group(1)
        name_m = _NAME_RE.search(block)
        if not name_m:
            continue
        stages_m = _STAGES_RE.search(block)
        stages = (
            [s.strip() for s in stages_m.group(1).split(",") if s.strip()]
            if stages_m else []
        )
        model_m = _MODEL_RE.search(block)
        out[name_m.group(1)] = {
            "model": model_m.group(1) if model_m else None,
            "css_stages": stages,
            "path": str(md),
        }
    return out


def domain_specialists(agents: dict[str, dict]) -> set[str]:
    """Names whose css_stages include both ``review`` and ``execute``."""
    return {
        name for name, meta in agents.items()
        if _DOMAIN_STAGES.issubset(set(meta["css_stages"]))
    }


def parse_dispatch_specialists(executor_md_path) -> set[str]:
    """css-* names referenced inside the <Domain_Dispatch_Table> section."""
    section = _DISPATCH_SECTION.search(
        Path(executor_md_path).read_text(encoding="utf-8"))
    return set(_CSS_NAME.findall(section.group(1))) if section else set()


def parse_readme_specialists(readme_md_path) -> set[str]:
    """css-* names in the first cell of a README table row (specialist table)."""
    return set(_README_ROW.findall(
        Path(readme_md_path).read_text(encoding="utf-8")))


def check_consistency(repo_root) -> list[str]:
    """Return human-readable drift messages (empty list == consistent)."""
    root = Path(repo_root)
    agents = parse_agent_files(root / "agents")
    all_names = set(agents)
    domain = domain_specialists(agents)
    dispatch = parse_dispatch_specialists(root / "agents" / "executor.md")
    readme_ko = parse_readme_specialists(root / "README.md")
    readme_en = parse_readme_specialists(root / "README.en.md")

    errors: list[str] = []
    # 1. dispatch table must list exactly the domain specialists.
    for name in sorted(domain - dispatch):
        errors.append(
            f"domain specialist {name!r} missing from executor Domain_Dispatch_Table")
    for name in sorted(dispatch - domain):
        errors.append(
            f"dispatch table references {name!r} which is not a domain agent "
            f"(missing agents/*.md or css_stages lacks review+execute)")
    # 2. every domain specialist documented in both README tables.
    for name in sorted(domain - readme_ko):
        errors.append(f"domain specialist {name!r} missing from README.md specialist table")
    for name in sorted(domain - readme_en):
        errors.append(f"domain specialist {name!r} missing from README.en.md specialist table")
    # 3. READMEs must not reference a non-existent agent.
    for name in sorted(readme_ko - all_names):
        errors.append(f"README.md references {name!r} which has no agents/*.md file")
    for name in sorted(readme_en - all_names):
        errors.append(f"README.en.md references {name!r} which has no agents/*.md file")
    return errors


def check_semantic_contracts(repo_root) -> list[str]:
    """Return prompt-contract drift that name-only registry checks cannot catch."""
    root = Path(repo_root)
    agents = parse_agent_files(root / "agents")
    domain = domain_specialists(agents)
    errors: list[str] = []

    specialist_markers = (
        "<CSS_Rich_Spec_Contract>",
        "artifact_paths",
        "Phase:",
        "RED command:",
        "GREEN command:",
        "Cross_Domain_Notes:",
        "ARTIFACT=<exact assigned path>",
        "write only inside the supplied worktree",
    )
    forbidden_runtime_refs = (
        "oh-my-claudecode:",
        "/team",
        "document-specialist",
        "frontend-engineer",
        "consult writer",
    )
    for name in sorted(agents):
        path = Path(agents[name]["path"])
        body = _FRONTMATTER_RE.sub(
            "", path.read_text(encoding="utf-8"), count=1)
        for forbidden in forbidden_runtime_refs:
            if forbidden in body:
                errors.append(f"{name} has unavailable runtime reference {forbidden!r}")

    for name in sorted(domain):
        path = Path(agents[name]["path"])
        text = path.read_text(encoding="utf-8")
        body = _FRONTMATTER_RE.sub("", text, count=1)
        for marker in specialist_markers:
            if marker not in body:
                errors.append(f"{name} missing Rich Spec contract marker {marker!r}")
        if body.count("<CSS_Rich_Spec_Contract>") != 1 or body.count(
            "</CSS_Rich_Spec_Contract>"
        ) != 1:
            errors.append(f"{name} must contain one balanced CSS_Rich_Spec_Contract")
        if body.count("<Domain_Notes_Reference>") != body.count(
            "</Domain_Notes_Reference>"
        ):
            errors.append(f"{name} has unbalanced Domain_Notes_Reference tags")

    required_by_file = {
        "commands/phase.md": ("--session", "single_phase:true", "parent_session"),
        "commands/interview.md": ('kind:"epic"', "single_phase:false"),
        "commands/plan.md": ("single_phase == true", "parent_session"),
        "commands/review.md": ("artifact_paths", "rich_specs", "advisories"),
        "commands/execute.md": ("rich_specs", "RED command", "GREEN command", "go.mod"),
        "commands/verify.md": ("rich_specs", "GREEN command"),
        "commands/pr.md": ("parent_session", "session.base_branch"),
        "commands/ship.md": ("/css:phase --session", ".claude/css/"),
        "agents/reviewer.md": ("artifact_paths", "advisory", "RED command:"),
        "agents/executor.md": ("rich_specs", "RED command", "GREEN command"),
        "agents/verifier.md": ("rich_specs", "GREEN command"),
    }
    for rel, markers in required_by_file.items():
        text = (root / rel).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{rel} missing pipeline contract marker {marker!r}")

    phase = (root / "commands" / "phase.md").read_text(encoding="utf-8")
    execute = (root / "commands" / "execute.md").read_text(encoding="utf-8")
    if "tools/css_schema" in phase:
        errors.append("commands/phase.md has unresolved repo-local tools/css_schema dependency")
    if "Language Detection Logic" in execute:
        errors.append("commands/execute.md has unresolved Language Detection Logic dependency")
    return errors
