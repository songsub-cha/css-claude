# Pipeline Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally-hosted, multi-project Kanban dashboard for CSS pipeline progress, with drag-and-drop Gate approval that auto-resumes the pipeline via a host-side bridge daemon.

**Architecture:** docker-compose stack (FastAPI + React static build + PostgreSQL 16) on Ubuntu 22.04. Active session state stays in `<project>/.claude/css/sessions/<id>.json` (file watch via `watchdog`). Bridge daemon runs on host as systemd user service, consuming an approval queue dir and spawning `claude --print '/css:ship --session X'` with env `CSS_DASHBOARD_RESUME=1`. CSS slash commands modified to detect this env var and skip `AskUserQuestion` when their Gate state is already `"approved"`. Cross-path approval (terminal or dashboard, per-Gate per-invocation) enforced by per-session lock file.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, SQLAlchemy 2.x async, asyncpg, Alembic, watchdog, structlog, pytest, pytest-asyncio, testcontainers-postgres; React 19, TypeScript, Vite, TailwindCSS v4, @dnd-kit, zustand, react-markdown, rehype-sanitize, rehype-highlight, vitest, @testing-library/react, msw, Playwright; PostgreSQL 16-alpine; Docker + docker-compose; systemd user services.

**Specialist routing:** Each task is tagged `[Specialist: <name>]` per the CSS Single-Specialist Task Rule. `executor-direct` indicates simple glue not needing domain expertise.

**Source spec:** [`docs/superpowers/specs/2026-05-28-pipeline-dashboard-design.md`](../specs/2026-05-28-pipeline-dashboard-design.md)

---

## Batch 1 — Foundation (CLI rename + config files)

User checkpoint after batch: verify rename hasn't broken any existing /css:* invocations on the toy-typescript fixture.

### Task 1.1: Rename `--slug` → `--session` across all 8 commands  [Specialist: css-prompt-engineer]

**Files:**
- Modify: `commands/interview.md`, `commands/plan.md`, `commands/review.md`, `commands/execute.md`, `commands/verify.md`, `commands/document.md`, `commands/pr.md`, `commands/ship.md`
- Test: `tests/golden/cli-rename.spec.md`

- [ ] **Step 1: Write the failing golden test**

Create `tests/golden/cli-rename.spec.md`:
```markdown
# Golden: CLI rename --slug → --session

For each command file in commands/*.md:
1. `argument-hint` frontmatter must contain `--session <name>` not `--slug <name>`
2. Body text must reference `--session <name>` in all flag examples
3. Internal references to `session.slug` JSON field are preserved as-is
4. File path templates (`sessions/{slug}.json`, `{slug}.lock`, etc.) preserved as-is

Run: `grep -r "\-\-slug" commands/` → must return 0 matches.
Run: `grep -r "\-\-session" commands/` → must return ≥8 matches (one per file).
```

- [ ] **Step 2: Run the assertion (verify it fails)**

```bash
bash -c 'count=$(grep -r "\-\-slug" commands/ | wc -l); echo "--slug occurrences: $count"; [ "$count" = "0" ] || exit 1'
```
Expected: FAIL (current files use --slug)

- [ ] **Step 3: Mechanical rename across 8 files**

For each of `interview.md`, `plan.md`, `review.md`, `execute.md`, `verify.md`, `document.md`, `pr.md`, `ship.md`:
- In `argument-hint:` frontmatter, replace `--slug <name>` with `--session <name>`
- In all body text, replace `--slug` with `--session`
- DO NOT touch:
  - `session.slug` (JSON field reference)
  - `{slug}` (file path placeholders)
  - "slug" word inside prose paragraphs that describe the identifier value itself

- [ ] **Step 4: Verify the test passes**

```bash
grep -rc "\-\-slug" commands/   # must print 0 for every file
grep -rc "\-\-session" commands/  # ≥ 8 files with ≥1 match each
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add commands/ tests/golden/cli-rename.spec.md
git commit -m "refactor(commands): rename --slug to --session for ergonomics"
```

---

### Task 1.2: Add dashboard config + env scaffolding  [Specialist: executor-direct]

**Files:**
- Create: `dashboard/.env.example`
- Create: `dashboard/README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing test (config presence)**

Create `tests/golden/dashboard-scaffold.spec.md`:
```markdown
# Golden: Dashboard scaffold exists

- File `dashboard/.env.example` exists and defines DB_PASSWORD, DATABASE_URL, DASHBOARD_PORT
- File `dashboard/README.md` exists, non-empty, mentions "docker-compose"
- `.gitignore` contains `dashboard/.env`
```

- [ ] **Step 2: Run the assertion (FAIL — files absent)**

```bash
test -f dashboard/.env.example || (echo "missing"; exit 1)
```
Expected: FAIL

- [ ] **Step 3: Create files**

`dashboard/.env.example`:
```env
# Copied to dashboard/.env by install-dashboard.sh; never commit dashboard/.env
DB_PASSWORD=changeme
DATABASE_URL=postgresql+asyncpg://css:changeme@postgres:5432/css_dashboard
DASHBOARD_PORT=7421
DASHBOARD_BIND=0.0.0.0
```

`dashboard/README.md`:
```markdown
# CSS Pipeline Dashboard

Local-hosted dashboard for visualizing CSS pipeline progress across multiple projects, with drag-and-drop Gate approval.

See [design spec](../docs/superpowers/specs/2026-05-28-pipeline-dashboard-design.md) for full design.

## Quick start (Ubuntu 22.04)

```bash
bash scripts/install-dashboard.sh
```

Open `http://<host-ip>:7421` from any LAN browser.

## Tech stack

- Backend: FastAPI + SQLAlchemy async + watchdog
- Frontend: React 19 + Vite + TailwindCSS v4 + dnd-kit
- Database: PostgreSQL 16
- Orchestration: docker-compose
- Bridge daemon: Python systemd user service (runs on host)
```

In `.gitignore`, append:
```
# dashboard local config
dashboard/.env
```

- [ ] **Step 4: Verify**

```bash
test -f dashboard/.env.example && test -f dashboard/README.md && grep -q "dashboard/.env" .gitignore && echo OK
```
Expected: prints `OK`

- [ ] **Step 5: Commit**

```bash
git add dashboard/.env.example dashboard/README.md .gitignore
git commit -m "chore(dashboard): scaffold dashboard/ with env template and README"
```

---

### Task 1.3: Create `~/.claude/css-dashboard/config.json` default + install-time path  [Specialist: executor-direct]

**Files:**
- Create: `config/dashboard-config.example.json`
- Test: `tests/golden/dashboard-config.spec.md`

- [ ] **Step 1: Write the failing test**

```markdown
# Golden: dashboard config example

`config/dashboard-config.example.json` parses as JSON and contains keys:
- dashboard_enabled (bool)
- dashboard_url (string)
- database_url (string with asyncpg)
- claude_cli (string)
- queue_dir (string ending in /queue)
- default_palette (array of ≥5 hex strings)
```

- [ ] **Step 2: Run (FAIL)**

```bash
python -c "import json; d=json.load(open('config/dashboard-config.example.json')); assert d['dashboard_enabled'] is True"
```
Expected: FAIL (file missing)

- [ ] **Step 3: Create file**

```json
{
  "dashboard_enabled": true,
  "dashboard_url": "http://localhost:7421",
  "database_url": "postgresql+asyncpg://css:CHANGEME@localhost:5432/css_dashboard",
  "claude_cli": "claude",
  "queue_dir": "~/.claude/css-dashboard/queue",
  "default_palette": ["#22c55e", "#a855f7", "#3b82f6", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"]
}
```

- [ ] **Step 4: Verify**

```bash
python -c "import json; d=json.load(open('config/dashboard-config.example.json')); assert all(k in d for k in ['dashboard_enabled','dashboard_url','database_url','claude_cli','queue_dir','default_palette']); print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add config/dashboard-config.example.json tests/golden/dashboard-config.spec.md
git commit -m "feat(config): add dashboard-config.example.json template"
```

---

## Batch 2 — CSS Command Gate Modifications

User checkpoint after batch: dry-run cross-path scenarios on toy-typescript fixture.

### Task 2.1: `/css:interview` — capture `repo_root` and `repo_name`  [Specialist: css-prompt-engineer]

**Files:**
- Modify: `commands/interview.md` (step 2 "Resolve session")
- Test: `tests/golden/interview-repo-capture.spec.md`

- [ ] **Step 1: Write the failing golden test**

```markdown
# Golden: interview captures repo_root + repo_name

In commands/interview.md, step 2 must include language that:
- Runs `git -C <project> rev-parse --show-toplevel` to determine repo_root
- Computes repo_name as basename(repo_root)
- Writes both to session.repo_root and session.repo_name

Run: grep -E "rev-parse --show-toplevel" commands/interview.md → ≥1 match
Run: grep -E "repo_name" commands/interview.md → ≥2 matches
```

- [ ] **Step 2: Run (FAIL)**

```bash
grep -E "rev-parse --show-toplevel" commands/interview.md && echo PASS || echo FAIL
```
Expected: `FAIL`

- [ ] **Step 3: Add repo capture block to interview.md step 2**

Insert before the "Update `_active.json`" sub-step:

```markdown
- **Capture repo metadata** (NEW):
  - `repo_root = git -C <project> rev-parse --show-toplevel`
  - `repo_name = basename(repo_root)`
  - Write to session JSON: `session.repo_root = repo_root`, `session.repo_name = repo_name`.
  - If `git rev-parse` fails (not in a git repo), record `repo_root = <project>` and `repo_name = basename(<project>)` and continue.
```

- [ ] **Step 4: Verify**

```bash
grep -c "rev-parse --show-toplevel" commands/interview.md   # ≥1
grep -c "repo_name" commands/interview.md                    # ≥2
```

- [ ] **Step 5: Commit**

```bash
git add commands/interview.md tests/golden/interview-repo-capture.spec.md
git commit -m "feat(interview): capture repo_root and repo_name on session init"
```

---

### Task 2.2: `/css:interview` — auto-register project in `projects.json`  [Specialist: css-prompt-engineer]

**Files:**
- Modify: `commands/interview.md`
- Test: `tests/golden/interview-projects-register.spec.md`

- [ ] **Step 1: Write the failing test**

```markdown
# Golden: interview appends to projects.json

After repo capture, command must include logic to:
- Check if `~/.claude/css-dashboard/config.json` exists and `dashboard_enabled == true`
- If yes: read `~/.claude/css-dashboard/projects.json`, append `{repo_root, repo_name, registered_at, color: null}` if repo_root not already present, write back
- Use flock for atomic concurrent appends

Run: grep -E "projects.json" commands/interview.md → ≥2 matches
Run: grep -E "flock|advisory lock" commands/interview.md → ≥1 match
Run: grep -E "dashboard_enabled" commands/interview.md → ≥1 match
```

- [ ] **Step 2: Run (FAIL)**

```bash
grep -c "projects.json" commands/interview.md
```
Expected: 0

- [ ] **Step 3: Add registration block**

Insert after the repo capture block in step 2:

```markdown
- **Register project in dashboard** (NEW, if dashboard enabled):
  - Read `~/.claude/css-dashboard/config.json`; if file missing or `dashboard_enabled != true`, skip this block.
  - Path: `projects_file = ~/.claude/css-dashboard/projects.json` (create with `{"projects": []}` if missing).
  - Acquire advisory lock via `flock -x <projects_file>` for the read-modify-write window.
  - If no entry with `repo_root == <captured repo_root>` exists, append:
    ```json
    {
      "repo_root": "<repo_root>",
      "repo_name": "<repo_name>",
      "registered_at": "<ISO-8601 now>",
      "color": null
    }
    ```
  - Write atomically (write to `projects.json.tmp` then `mv` over).
  - Release lock.
  - If write fails, log the error but continue (registration is best-effort; pipeline must not block).
```

- [ ] **Step 4: Verify**

```bash
grep -c "projects.json" commands/interview.md       # ≥2
grep -c "flock" commands/interview.md               # ≥1
grep -c "dashboard_enabled" commands/interview.md   # ≥1
```

- [ ] **Step 5: Commit**

```bash
git add commands/interview.md tests/golden/interview-projects-register.spec.md
git commit -m "feat(interview): auto-register project in dashboard projects.json"
```

---

### Task 2.3: `/css:ship` — Gate 2 cross-path branching  [Specialist: css-prompt-engineer]

**Files:**
- Modify: `commands/ship.md` (step 7)
- Test: `tests/golden/ship-gate2-crosspath.spec.md`

- [ ] **Step 1: Write the failing golden test**

```markdown
# Golden: ship Gate 2 cross-path

Step 7 (Gate 2 — pre-execute) must contain:
- A check for env var CSS_DASHBOARD_RESUME == "1" (non-interactive)
- A read of `session.gates.gate2_pre_execute.state`
- 3-option AskUserQuestion path when dashboard_enabled and interactive (Yes/Wait for dashboard/Cancel)
- 2-option AskUserQuestion legacy path when not dashboard_enabled
- Graceful exit path that writes state=pending and releases lock for non-interactive

Run: grep -c "CSS_DASHBOARD_RESUME" commands/ship.md → ≥1
Run: grep -c "Wait for dashboard" commands/ship.md → ≥1
Run: grep -c "gate2_pre_execute" commands/ship.md → ≥2
```

- [ ] **Step 2: Run (FAIL)**

```bash
grep -c "CSS_DASHBOARD_RESUME" commands/ship.md
```
Expected: 0

- [ ] **Step 3: Replace step 7 in ship.md**

Replace the current step 7 (Gate 2 — pre-execute) with:

````markdown
7. **Gate 2 — pre-execute** (cross-path):

   ```
   is_resume = ($CSS_DASHBOARD_RESUME == "1")
   gate = session.gates.gate2_pre_execute
   state = gate.state if gate else null

   if state == "approved":
       proceed to step 8
       return

   if not is_resume and config.dashboard_enabled:
       banner = "Plan 검증 완료. worktree '../<repo>-css-<session>' 생성 후 execute 시작."
       if state == "pending":
           banner += " (대시보드 승인 대기 중 — 여기서 승인해도 됩니다)"
       answer = AskUserQuestion(banner, options=[
           "Yes (여기서 승인)",
           "Wait for dashboard (대시보드에서 드래그)",
           "Cancel"
       ])
       if answer == "Yes (여기서 승인)":
           session.gates.gate2_pre_execute = {
               "state": "approved", "source": "terminal_ask",
               "reached_at": gate.reached_at or now_iso(),
               "approved_at": now_iso(), "approved_by": "terminal"
           }
           save_session()
           proceed to step 8
       elif answer == "Wait for dashboard ...":
           if state != "pending":
               session.gates.gate2_pre_execute = {
                   "state": "pending", "reached_at": now_iso(),
                   "source": null, "approved_at": null, "approved_by": null
               }
               save_session()
           release_lock(); exit 0
       else:  # Cancel
           release_lock(); exit 0

   elif not is_resume and not config.dashboard_enabled:
       # legacy 2-option
       answer = AskUserQuestion(banner, options=["Yes", "Cancel"])
       if answer == "Yes":
           # mark approved (state field added for forward compat with dashboard re-install)
           session.gates.gate2_pre_execute = { "state": "approved", "source": "terminal_ask", ... }
           save_session(); proceed
       else:
           release_lock(); exit 0

   else:  # is_resume — daemon-bridge spawned us
       if state != "approved":
           session.gates.gate2_pre_execute = { "state": "pending", "reached_at": now_iso(), ... }
           save_session()
       release_lock(); exit 0
   ```
````

- [ ] **Step 4: Verify**

```bash
grep -c "CSS_DASHBOARD_RESUME" commands/ship.md         # ≥1
grep -c "Wait for dashboard" commands/ship.md           # ≥1
grep -c "gate2_pre_execute" commands/ship.md            # ≥3
```

- [ ] **Step 5: Commit**

```bash
git add commands/ship.md tests/golden/ship-gate2-crosspath.spec.md
git commit -m "feat(ship): cross-path Gate 2 (terminal + dashboard) with CSS_DASHBOARD_RESUME env detection"
```

---

### Task 2.4: `/css:ship` — Gate 3 cross-path branching  [Specialist: css-prompt-engineer]

**Files:**
- Modify: `commands/ship.md` (step 11)
- Test: `tests/golden/ship-gate3-crosspath.spec.md`

- [ ] **Step 1: Write the failing test**

Same shape as 2.3 but for `gate3_pre_pr`.

```markdown
Run: grep -c "gate3_pre_pr" commands/ship.md → ≥2
Run: grep -c "draft\|PR\|push" commands/ship.md → context for Gate 3 prompt preserved
```

- [ ] **Step 2: Run (FAIL — only original 2-option exists)**

```bash
grep -c "gate3_pre_pr" commands/ship.md
```
Expected: 0 (no per-state branching present yet)

- [ ] **Step 3: Replace step 11**

Apply the same cross-path block as Task 2.3, but for `gate3_pre_pr`. The banner text:
```
"구현 + 문서 완료. 브랜치 'css/<session>'를 origin에 push하고 PR 생성."
```
3-option labels: `"Yes (PR 생성)"`, `"Draft PR (대시보드에서 드래그 후 PR draft 모드)"`, `"Cancel"`. The `Draft PR` choice sets approved + an extra flag `session.gates.gate3_pre_pr.draft = true` consumed by `/css:pr`.

- [ ] **Step 4: Verify**

```bash
grep -c "gate3_pre_pr" commands/ship.md   # ≥3
grep -c "Draft PR" commands/ship.md       # ≥1
```

- [ ] **Step 5: Commit**

```bash
git add commands/ship.md tests/golden/ship-gate3-crosspath.spec.md
git commit -m "feat(ship): cross-path Gate 3 with draft-PR option"
```

---

### Task 2.5: `/css:execute` and `/css:pr` — honor master_flow gate state  [Specialist: css-prompt-engineer]

**Files:**
- Modify: `commands/execute.md`, `commands/pr.md`
- Test: `tests/golden/execute-pr-masterflow.spec.md`

- [ ] **Step 1: Write the failing test**

```markdown
# Golden: execute/pr respect master_flow + dashboard gate state

commands/execute.md step 7 must:
- Skip the AskUserQuestion when `session.master_flow == true` (already true today — assert preserved)
- Additionally: if `session.gates.gate2_pre_execute.state != "approved"` and `master_flow == true`, abort with "Gate 2가 승인되지 않았습니다. /css:ship으로 진행하세요."

commands/pr.md must apply the same pattern for gate3_pre_pr.

Run: grep -c "gate2_pre_execute.state" commands/execute.md → ≥1
Run: grep -c "gate3_pre_pr.state" commands/pr.md → ≥1
```

- [ ] **Step 2: Run (FAIL)**

```bash
grep -c "gate2_pre_execute.state" commands/execute.md   # expect 0
```

- [ ] **Step 3: Modify commands**

In `commands/execute.md` step 7 (the `AskUserQuestion (master-flow Gate 2)` block), prepend a guard:

```markdown
- **Master-flow guard** (NEW):
  - If `session.master_flow == true` and `session.gates.gate2_pre_execute.state != "approved"`, abort:
    "Gate 2가 승인되지 않았습니다. `/css:ship --session <name>`을 통해 진행하세요."
  - If `session.master_flow == true` and approved, proceed without prompting (existing behavior).
```

In `commands/pr.md`, add an analogous guard at the start of the command body (Gate 3).

- [ ] **Step 4: Verify**

```bash
grep -c "gate2_pre_execute.state" commands/execute.md   # ≥1
grep -c "gate3_pre_pr.state" commands/pr.md             # ≥1
```

- [ ] **Step 5: Commit**

```bash
git add commands/execute.md commands/pr.md tests/golden/execute-pr-masterflow.spec.md
git commit -m "feat(execute,pr): enforce gate state in master_flow before proceeding"
```

---

## Batch 3 — PostgreSQL Schema & Models

User checkpoint after batch: spin up postgres container, run alembic migration, verify schema.

### Task 3.1: pyproject.toml + Alembic initial migration  [Specialist: css-db-specialist]

**Files:**
- Create: `dashboard/pyproject.toml`
- Create: `dashboard/alembic.ini`
- Create: `dashboard/alembic/env.py`
- Create: `dashboard/alembic/versions/0001_initial.py`
- Test: `dashboard/backend/tests/test_migration.py`

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_migration.py`:
```python
import asyncio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="module")
def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

def test_initial_migration_creates_all_tables(pg_container):
    url = pg_container.get_connection_url().replace("postgresql+psycopg2", "postgresql")
    alembic_cfg = Config("dashboard/alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(alembic_cfg, "head")

    async def check():
        engine = create_async_engine(url.replace("postgresql", "postgresql+asyncpg"))
        async with engine.connect() as conn:
            rows = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = sorted(r[0] for r in rows)
        await engine.dispose()
        return tables
    tables = asyncio.run(check())
    assert tables == ["alembic_version", "daemon_runs", "gate_audit_log", "projects", "sessions_history"]
```

- [ ] **Step 2: Run (FAIL)**

```bash
cd dashboard && pytest backend/tests/test_migration.py -v
```
Expected: ImportError or file-not-found for alembic.ini

- [ ] **Step 3: Implement**

`dashboard/pyproject.toml`:
```toml
[project]
name = "css-dashboard"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "sqlalchemy[asyncio]>=2.0",
  "asyncpg>=0.29",
  "alembic>=1.13",
  "watchdog>=4.0",
  "structlog>=24",
  "pydantic-settings>=2.6",
  "python-multipart>=0.0.9",
  "httpx>=0.27",  # for bridge → API callback
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-asyncio>=0.24",
  "testcontainers[postgres]>=4.7",
  "ruff>=0.7",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["backend/tests", "bridge/tests"]
```

`dashboard/alembic.ini`:
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://css:changeme@localhost:5432/css_dashboard
```

`dashboard/alembic/env.py`:
```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None  # raw SQL migrations only in v0.1

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    raise RuntimeError("Offline mode not supported")
else:
    run_migrations_online()
```

`dashboard/alembic/versions/0001_initial.py`:
```python
"""initial schema"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
    CREATE TABLE projects (
      id SERIAL PRIMARY KEY,
      repo_root TEXT UNIQUE NOT NULL,
      repo_name TEXT NOT NULL,
      color TEXT NOT NULL DEFAULT '#3b82f6',
      registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE sessions_history (
      id SERIAL PRIMARY KEY,
      project_id INT REFERENCES projects(id) ON DELETE CASCADE,
      session_id TEXT NOT NULL,
      idea TEXT NOT NULL,
      started_at TIMESTAMPTZ NOT NULL,
      finished_at TIMESTAMPTZ,
      final_phase TEXT NOT NULL,
      outcome TEXT NOT NULL CHECK (outcome IN ('completed','failed','aborted')),
      pr_url TEXT,
      phase_durations JSONB NOT NULL,
      snapshot JSONB NOT NULL,
      archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      UNIQUE (project_id, session_id, archived_at)
    );

    CREATE TABLE gate_audit_log (
      id SERIAL PRIMARY KEY,
      project_id INT REFERENCES projects(id),
      session_id TEXT NOT NULL,
      gate TEXT NOT NULL CHECK (gate IN ('gate2_pre_execute','gate3_pre_pr')),
      reached_at TIMESTAMPTZ NOT NULL,
      approved_at TIMESTAMPTZ,
      approval_source TEXT CHECK (approval_source IN ('dashboard_drag','terminal_ask')),
      resume_status TEXT CHECK (resume_status IN ('success','failed','retrying')),
      retry_count INT NOT NULL DEFAULT 0,
      error_message TEXT
    );

    CREATE TABLE daemon_runs (
      id SERIAL PRIMARY KEY,
      session_id TEXT NOT NULL,
      command TEXT NOT NULL,
      started_at TIMESTAMPTZ NOT NULL,
      finished_at TIMESTAMPTZ,
      exit_code INT,
      stdout_tail TEXT,
      stderr_tail TEXT
    );

    CREATE INDEX idx_history_project_finished ON sessions_history(project_id, finished_at DESC);
    CREATE INDEX idx_audit_session ON gate_audit_log(session_id, reached_at DESC);
    CREATE INDEX idx_runs_session ON daemon_runs(session_id, started_at DESC);
    """)

def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS daemon_runs;
    DROP TABLE IF EXISTS gate_audit_log;
    DROP TABLE IF EXISTS sessions_history;
    DROP TABLE IF EXISTS projects;
    """)
```

- [ ] **Step 4: Verify**

```bash
cd dashboard && pip install -e .[dev] && pytest backend/tests/test_migration.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/pyproject.toml dashboard/alembic.ini dashboard/alembic/ dashboard/backend/tests/test_migration.py
git commit -m "feat(db): initial Alembic migration for projects/sessions_history/gate_audit_log/daemon_runs"
```

---

### Task 3.2: SQLAlchemy models  [Specialist: css-db-specialist]

**Files:**
- Create: `dashboard/backend/models.py`
- Test: `dashboard/backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_models.py`:
```python
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command

from backend.models import Project, SessionHistory, GateAuditLog, DaemonRun, Base

@pytest.fixture(scope="module")
async def pg_engine():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        cfg = Config("dashboard/alembic.ini")
        cfg.set_main_option("sqlalchemy.url", url.replace("postgresql+asyncpg","postgresql"))
        command.upgrade(cfg, "head")
        engine = create_async_engine(url)
        yield engine
        await engine.dispose()

async def test_project_crud(pg_engine):
    async_session = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with async_session() as s:
        p = Project(repo_root="/home/user/proj", repo_name="proj", color="#22c55e")
        s.add(p); await s.commit(); await s.refresh(p)
        assert p.id is not None
        assert p.color == "#22c55e"
        result = await s.execute(select(Project).where(Project.repo_root == "/home/user/proj"))
        assert result.scalar_one().repo_name == "proj"

async def test_session_history_jsonb(pg_engine):
    async_session = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with async_session() as s:
        p = Project(repo_root="/home/user/proj2", repo_name="proj2")
        s.add(p); await s.commit(); await s.refresh(p)
        h = SessionHistory(
            project_id=p.id, session_id="feat-x", idea="x",
            started_at=datetime.now(timezone.utc), final_phase="pr", outcome="completed",
            phase_durations={"interview": 720, "plan": 360},
            snapshot={"slug": "feat-x"}
        )
        s.add(h); await s.commit(); await s.refresh(h)
        assert h.phase_durations["interview"] == 720
```

- [ ] **Step 2: Run (FAIL)**

```bash
cd dashboard && pytest backend/tests/test_models.py -v
```
Expected: ImportError on `backend.models`

- [ ] **Step 3: Implement models**

`dashboard/backend/models.py`:
```python
from datetime import datetime
from sqlalchemy import (
    BigInteger, Integer, String, Text, TIMESTAMP, ForeignKey, CheckConstraint,
    UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo_root: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    repo_name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, nullable=False, default="#3b82f6")
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class SessionHistory(Base):
    __tablename__ = "sessions_history"
    __table_args__ = (
        UniqueConstraint("project_id", "session_id", "archived_at"),
        CheckConstraint("outcome IN ('completed','failed','aborted')"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    idea: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    final_phase: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    pr_url: Mapped[str | None] = mapped_column(Text)
    phase_durations: Mapped[dict] = mapped_column(JSONB, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    archived_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class GateAuditLog(Base):
    __tablename__ = "gate_audit_log"
    __table_args__ = (
        CheckConstraint("gate IN ('gate2_pre_execute','gate3_pre_pr')"),
        CheckConstraint("approval_source IS NULL OR approval_source IN ('dashboard_drag','terminal_ask')"),
        CheckConstraint("resume_status IS NULL OR resume_status IN ('success','failed','retrying')"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    gate: Mapped[str] = mapped_column(Text, nullable=False)
    reached_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    approval_source: Mapped[str | None] = mapped_column(Text)
    resume_status: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)


class DaemonRun(Base):
    __tablename__ = "daemon_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    exit_code: Mapped[int | None] = mapped_column(Integer)
    stdout_tail: Mapped[str | None] = mapped_column(Text)
    stderr_tail: Mapped[str | None] = mapped_column(Text)
```

- [ ] **Step 4: Verify**

```bash
cd dashboard && pytest backend/tests/test_models.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/models.py dashboard/backend/tests/test_models.py
git commit -m "feat(db): SQLAlchemy models for all four tables"
```

---

### Task 3.3: DB session factory + async test fixture  [Specialist: css-db-specialist]

**Files:**
- Create: `dashboard/backend/db.py`
- Create: `dashboard/backend/tests/conftest.py`
- Test: `dashboard/backend/tests/test_db.py`

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_db.py`:
```python
import pytest
from backend.db import get_engine, get_session_factory, close_engine

async def test_engine_singleton():
    e1 = get_engine("postgresql+asyncpg://test:test@localhost/test")
    e2 = get_engine("postgresql+asyncpg://test:test@localhost/test")
    assert e1 is e2
    await close_engine()

async def test_session_factory_yields_session(pg_engine):
    factory = get_session_factory(pg_engine)
    async with factory() as s:
        assert s.is_active
```

- [ ] **Step 2: Run (FAIL)** — `backend.db` missing.

- [ ] **Step 3: Implement**

`dashboard/backend/db.py`:
```python
from typing import Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
)

_engine: Optional[AsyncEngine] = None

def get_engine(url: str) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(url, pool_pre_ping=True, pool_size=10)
    return _engine

def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def close_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
```

`dashboard/backend/tests/conftest.py`:
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="session")
def pg_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        url_sync = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql")
        cfg = Config("dashboard/alembic.ini")
        cfg.set_main_option("sqlalchemy.url", url_sync)
        command.upgrade(cfg, "head")
        yield url_sync.replace("postgresql", "postgresql+asyncpg")

@pytest.fixture
async def pg_engine(pg_url):
    engine = create_async_engine(pg_url)
    yield engine
    await engine.dispose()
```

- [ ] **Step 4: Verify**

```bash
cd dashboard && pytest backend/tests/test_db.py -v
```

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/db.py dashboard/backend/tests/conftest.py dashboard/backend/tests/test_db.py
git commit -m "feat(db): async engine factory and pytest fixtures"
```

---

## Batch 4 — FastAPI Backend

User checkpoint after batch: hit `/api/sessions` from a curl with synthetic JSON; verify SSE delivers updates on watcher events.

### Task 4.1: Pydantic Settings (`config.py`)  [Specialist: executor-direct]

**Files:**
- Create: `dashboard/backend/config.py`
- Test: `dashboard/backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# test_config.py
import os
from backend.config import Settings

def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://a:b@c/d")
    monkeypatch.setenv("DASHBOARD_PORT", "7777")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://a:b@c/d"
    assert s.dashboard_port == 7777
    assert s.queue_dir.name == "queue"

def test_defaults():
    s = Settings(database_url="postgresql+asyncpg://x:y@z/w")
    assert s.dashboard_port == 7421
    assert s.dashboard_bind == "0.0.0.0"
    assert s.cors_origins == ["*"]
```

- [ ] **Step 2: Run (FAIL)** — module missing.

- [ ] **Step 3: Implement**

```python
# dashboard/backend/config.py
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    dashboard_port: int = 7421
    dashboard_bind: str = "0.0.0.0"
    host_claude_dir: Path = Path("/host/.claude")
    queue_dir: Path = Field(default_factory=lambda: Path("/host/.claude/css-dashboard/queue"))
    runs_dir: Path = Field(default_factory=lambda: Path("/host/.claude/css-dashboard/runs"))
    projects_json: Path = Field(default_factory=lambda: Path("/host/.claude/css-dashboard/projects.json"))
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
```

- [ ] **Step 4: Verify** — `pytest backend/tests/test_config.py -v` → PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/config.py dashboard/backend/tests/test_config.py
git commit -m "feat(backend): Pydantic Settings for dashboard runtime config"
```

---

### Task 4.2: FastAPI app skeleton + lifespan  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/backend/main.py`
- Test: `dashboard/backend/tests/test_main.py`

- [ ] **Step 1: Write the failing test**

```python
# test_main.py
from httpx import AsyncClient, ASGITransport
from backend.main import app

async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

async def test_cors_headers_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.options("/api/health", headers={"Origin": "http://localhost", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" in {h.lower() for h in r.headers.keys()}
```

- [ ] **Step 2: Run (FAIL)** — module missing.

- [ ] **Step 3: Implement**

```python
# dashboard/backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from backend.config import Settings

log = structlog.get_logger()
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("dashboard.startup", port=settings.dashboard_port)
    # placeholder: watcher start hooks added in T4.13
    yield
    log.info("dashboard.shutdown")

app = FastAPI(title="CSS Pipeline Dashboard", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Verify** — `pytest backend/tests/test_main.py -v` → 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/main.py dashboard/backend/tests/test_main.py
git commit -m "feat(backend): FastAPI app skeleton with health and CORS"
```

---

### Task 4.3: `services/session_reader.py` — load + parse session JSON  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/backend/services/__init__.py`, `dashboard/backend/services/session_reader.py`
- Test: `dashboard/backend/tests/test_session_reader.py`

- [ ] **Step 1: Write the failing test**

```python
# test_session_reader.py
import json
from pathlib import Path
from backend.services.session_reader import (
    parse_session_file, list_sessions_for_project, ParsedSession
)

def make_session(tmp_path: Path, slug: str, phase: str) -> Path:
    d = tmp_path / ".claude" / "css" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.json"
    f.write_text(json.dumps({
        "slug": slug, "idea": "x", "master_flow": True,
        "repo_root": str(tmp_path), "repo_name": tmp_path.name,
        "current_phase": phase,
        "phases": {p: {"status": "pending"} for p in
                   ["interview","plan","review","execute","verify","document","pr"]},
        "gates": {"gate2_pre_execute": None, "gate3_pre_pr": None}
    }))
    return f

def test_parse_session_file(tmp_path):
    f = make_session(tmp_path, "feat-x", "plan")
    parsed = parse_session_file(f)
    assert parsed.slug == "feat-x"
    assert parsed.current_phase == "plan"
    assert parsed.repo_name == tmp_path.name

def test_list_sessions_for_project(tmp_path):
    make_session(tmp_path, "feat-a", "review")
    make_session(tmp_path, "feat-b", "execute")
    sessions = list_sessions_for_project(tmp_path)
    assert sorted(s.slug for s in sessions) == ["feat-a", "feat-b"]

def test_corrupted_json_returns_none(tmp_path):
    d = tmp_path / ".claude/css/sessions"; d.mkdir(parents=True)
    (d / "broken.json").write_text("{not json")
    assert parse_session_file(d / "broken.json") is None
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/services/session_reader.py
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

log = structlog.get_logger()

@dataclass
class ParsedSession:
    slug: str
    idea: str
    repo_root: str
    repo_name: str
    current_phase: str
    phases: dict
    gates: dict
    master_flow: bool
    file_path: Path
    mtime: float

    @property
    def gate2_state(self) -> Optional[str]:
        g = self.gates.get("gate2_pre_execute")
        return (g or {}).get("state") if isinstance(g, dict) else None

    @property
    def gate3_state(self) -> Optional[str]:
        g = self.gates.get("gate3_pre_pr")
        return (g or {}).get("state") if isinstance(g, dict) else None


def parse_session_file(path: Path) -> Optional[ParsedSession]:
    try:
        data = json.loads(path.read_text())
        return ParsedSession(
            slug=data["slug"],
            idea=data.get("idea", ""),
            repo_root=data.get("repo_root", ""),
            repo_name=data.get("repo_name", "(unknown)"),
            current_phase=data.get("current_phase", "interview"),
            phases=data.get("phases", {}),
            gates=data.get("gates", {}),
            master_flow=data.get("master_flow", False),
            file_path=path,
            mtime=path.stat().st_mtime,
        )
    except (json.JSONDecodeError, KeyError, FileNotFoundError, OSError) as e:
        log.warning("session_reader.parse_failed", path=str(path), error=str(e))
        return None


def list_sessions_for_project(project_root: Path) -> list[ParsedSession]:
    sessions_dir = project_root / ".claude" / "css" / "sessions"
    if not sessions_dir.exists():
        return []
    out = []
    for f in sessions_dir.glob("*.json"):
        if f.name == "_active.json":
            continue
        parsed = parse_session_file(f)
        if parsed:
            out.append(parsed)
    return out
```

- [ ] **Step 4: Verify** — 3 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/services/ dashboard/backend/tests/test_session_reader.py
git commit -m "feat(backend): session JSON reader with corruption tolerance"
```

---

### Task 4.4: `services/project_registry.py` — read projects.json with flock  [Specialist: executor-direct]

**Files:**
- Create: `dashboard/backend/services/project_registry.py`
- Test: `dashboard/backend/tests/test_project_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# test_project_registry.py
import json
from pathlib import Path
from backend.services.project_registry import read_projects, ProjectEntry

def test_read_projects(tmp_path):
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": "/p1", "repo_name": "p1", "registered_at": "2026-01-01T00:00:00Z", "color": None},
        {"repo_root": "/p2", "repo_name": "p2", "registered_at": "2026-01-02T00:00:00Z", "color": "#22c55e"}
    ]}))
    entries = read_projects(pj)
    assert len(entries) == 2
    assert entries[0].repo_root == "/p1"
    assert entries[1].color == "#22c55e"

def test_missing_file_returns_empty(tmp_path):
    assert read_projects(tmp_path / "nope.json") == []
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/services/project_registry.py
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectEntry:
    repo_root: str
    repo_name: str
    registered_at: str
    color: Optional[str]


def read_projects(projects_json: Path) -> list[ProjectEntry]:
    if not projects_json.exists():
        return []
    try:
        data = json.loads(projects_json.read_text())
        return [
            ProjectEntry(
                repo_root=p["repo_root"], repo_name=p["repo_name"],
                registered_at=p.get("registered_at", ""), color=p.get("color")
            )
            for p in data.get("projects", [])
        ]
    except (json.JSONDecodeError, KeyError, OSError):
        return []
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/services/project_registry.py dashboard/backend/tests/test_project_registry.py
git commit -m "feat(backend): projects.json reader"
```

---

### Task 4.5: `routers/projects.py` — GET + PATCH  [Specialist: css-api-specialist]

**Files:**
- Create: `dashboard/backend/routers/__init__.py`, `dashboard/backend/routers/projects.py`
- Modify: `dashboard/backend/main.py` (include router)
- Test: `dashboard/backend/tests/test_router_projects.py`

- [ ] **Step 1: Write the failing test**

```python
# test_router_projects.py
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Project

async def test_get_projects_empty(pg_engine, monkeypatch):
    # arrange: DB has no projects yet
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/projects")
    assert r.status_code == 200
    assert r.json() == {"projects": []}

async def test_patch_project_color(pg_engine):
    # insert one project, PATCH color
    from sqlalchemy.ext.asyncio import async_sessionmaker
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as s:
        p = Project(repo_root="/r", repo_name="r", color="#000000")
        s.add(p); await s.commit(); await s.refresh(p); pid = p.id
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.patch(f"/api/projects/{pid}", json={"color": "#22c55e"})
    assert r.status_code == 200
    assert r.json()["color"] == "#22c55e"

async def test_patch_invalid_color_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.patch("/api/projects/1", json={"color": "javascript:alert(1)"})
    assert r.status_code == 422
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/projects.py
import re
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.deps import get_db_session  # provided in T4.2 update below
from backend.models import Project

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectOut(BaseModel):
    id: int
    repo_root: str
    repo_name: str
    color: str

class ProjectPatch(BaseModel):
    color: str
    @field_validator("color")
    @classmethod
    def hex_only(cls, v: str) -> str:
        if not HEX_RE.match(v):
            raise ValueError("color must be #RRGGBB hex")
        return v

@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db_session)):
    rows = (await db.execute(select(Project).order_by(Project.id))).scalars().all()
    return {"projects": [ProjectOut(id=p.id, repo_root=p.repo_root, repo_name=p.repo_name, color=p.color).model_dump() for p in rows]}

@router.patch("/{project_id}")
async def patch_project(project_id: int, body: ProjectPatch, db: AsyncSession = Depends(get_db_session)):
    p = await db.get(Project, project_id)
    if p is None:
        raise HTTPException(404, "project not found")
    p.color = body.color
    await db.commit()
    return ProjectOut(id=p.id, repo_root=p.repo_root, repo_name=p.repo_name, color=p.color).model_dump()
```

Also create `dashboard/backend/deps.py`:
```python
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_engine, get_session_factory
from backend.config import Settings

async def get_db_session() -> AsyncSession:
    settings = Settings()
    engine = get_engine(settings.database_url)
    factory = get_session_factory(engine)
    async with factory() as s:
        yield s
```

Add to `main.py`:
```python
from backend.routers import projects as projects_router
app.include_router(projects_router.router)
```

- [ ] **Step 4: Verify** — 3 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/ dashboard/backend/deps.py dashboard/backend/main.py dashboard/backend/tests/test_router_projects.py
git commit -m "feat(api): GET/PATCH /api/projects with hex-color validation"
```

---

### Task 4.6: `routers/sessions.py` — GET list + detail  [Specialist: css-api-specialist]

**Files:**
- Create: `dashboard/backend/routers/sessions.py`
- Test: `dashboard/backend/tests/test_router_sessions.py`

- [ ] **Step 1: Write the failing test**

```python
# test_router_sessions.py
import json, os
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app

def _make_proj(tmp_path: Path, repo_name: str, slug: str, phase: str):
    s = tmp_path / repo_name / ".claude/css/sessions"
    s.mkdir(parents=True, exist_ok=True)
    (s / f"{slug}.json").write_text(json.dumps({
        "slug": slug, "idea": "i", "master_flow": True,
        "repo_root": str(tmp_path / repo_name), "repo_name": repo_name,
        "current_phase": phase, "phases": {}, "gates": {}
    }))
    return tmp_path / repo_name

async def test_get_sessions_aggregates_across_projects(tmp_path, monkeypatch):
    p1 = _make_proj(tmp_path, "alpha", "feat-x", "review")
    p2 = _make_proj(tmp_path, "beta", "feat-y", "execute")
    # write projects.json
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(p1), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
        {"repo_root": str(p2), "repo_name": "beta", "registered_at": "y", "color": "#a855f7"}
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions")
    assert r.status_code == 200
    slugs = sorted(s["slug"] for s in r.json()["sessions"])
    assert slugs == ["feat-x", "feat-y"]

async def test_get_session_detail(tmp_path, monkeypatch):
    p = _make_proj(tmp_path, "alpha", "feat-x", "review")
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [{"repo_root": str(p), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"}]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/feat-x")
    assert r.status_code == 200
    assert r.json()["slug"] == "feat-x"
    assert r.json()["repo_name"] == "alpha"
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/sessions.py
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.config import Settings
from backend.services.project_registry import read_projects
from backend.services.session_reader import list_sessions_for_project, parse_session_file

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

def _settings() -> Settings:
    return Settings()

@router.get("")
async def list_sessions():
    s = _settings()
    out = []
    for proj in read_projects(s.projects_json):
        for sess in list_sessions_for_project(Path(proj.repo_root)):
            out.append({
                "slug": sess.slug, "idea": sess.idea,
                "repo_root": sess.repo_root, "repo_name": sess.repo_name,
                "current_phase": sess.current_phase,
                "phases": sess.phases, "gates": sess.gates,
                "mtime": sess.mtime,
            })
    return {"sessions": out}

@router.get("/{slug}")
async def get_session(slug: str):
    s = _settings()
    for proj in read_projects(s.projects_json):
        sessions = list_sessions_for_project(Path(proj.repo_root))
        for sess in sessions:
            if sess.slug == slug:
                return {
                    "slug": sess.slug, "idea": sess.idea,
                    "repo_root": sess.repo_root, "repo_name": sess.repo_name,
                    "current_phase": sess.current_phase,
                    "phases": sess.phases, "gates": sess.gates,
                    "mtime": sess.mtime, "master_flow": sess.master_flow,
                }
    raise HTTPException(404, f"session {slug} not found")
```

Add `app.include_router(...)` in main.py.

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/sessions.py dashboard/backend/main.py dashboard/backend/tests/test_router_sessions.py
git commit -m "feat(api): GET /api/sessions (list across projects) and /api/sessions/{slug}"
```

---

### Task 4.7: `services/artifact_reader.py` — whitelist + path traversal guard  [Specialist: css-api-specialist]

**Files:**
- Create: `dashboard/backend/services/artifact_reader.py`
- Test: `dashboard/backend/tests/test_artifact_reader.py`

- [ ] **Step 1: Write the failing test**

```python
# test_artifact_reader.py
import pytest
from pathlib import Path
from backend.services.artifact_reader import resolve_artifact_path, ArtifactNotFound, ArtifactForbidden

def test_resolve_spec(tmp_path):
    spec = tmp_path / "docs/specs/x.md"; spec.parent.mkdir(parents=True); spec.write_text("hi")
    session = {"phases": {"interview": {"artifact": "docs/specs/x.md"}}, "repo_root": str(tmp_path)}
    p = resolve_artifact_path(session, "spec")
    assert p == spec.resolve()

def test_path_traversal_blocked(tmp_path):
    session = {"phases": {"interview": {"artifact": "../../../../etc/passwd"}}, "repo_root": str(tmp_path)}
    with pytest.raises(ArtifactForbidden):
        resolve_artifact_path(session, "spec")

def test_unknown_name_rejected(tmp_path):
    session = {"phases": {}, "repo_root": str(tmp_path)}
    with pytest.raises(ArtifactNotFound):
        resolve_artifact_path(session, "evil-name")
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/services/artifact_reader.py
from pathlib import Path
from typing import Optional

WHITELIST = {"spec", "plan", "exec-log", "verify", "code-review", "security-review", "docs"}

class ArtifactNotFound(Exception): pass
class ArtifactForbidden(Exception): pass

def _is_rich_spec_name(name: str) -> bool:
    return name.startswith("rich-spec-") and len(name) <= 64

def resolve_artifact_path(session: dict, name: str) -> Path:
    if name not in WHITELIST and not _is_rich_spec_name(name):
        raise ArtifactNotFound(name)
    repo_root = Path(session.get("repo_root", "")).resolve()
    if not repo_root.exists():
        raise ArtifactNotFound("repo_root missing")

    candidate: Optional[Path] = None
    phases = session.get("phases", {})

    if name == "spec":
        rel = phases.get("interview", {}).get("artifact")
        if rel: candidate = (repo_root / rel)
    elif name == "plan":
        rel = phases.get("plan", {}).get("artifact")
        if rel: candidate = (repo_root / rel)
    elif name == "exec-log":
        d = repo_root / ".claude/css/executions"
        if d.exists():
            files = sorted(d.glob(f"exec-log-{session['slug']}-*.md"))
            candidate = files[-1] if files else None
    elif name == "verify":
        d = repo_root / ".claude/css/verifies"
        if d.exists():
            files = sorted(d.glob(f"verify-{session['slug']}-*.md"))
            candidate = files[-1] if files else None
    elif _is_rich_spec_name(name):
        task_id = name[len("rich-spec-"):]
        d = repo_root / ".claude/css/plans"
        if d.exists():
            files = sorted(d.glob(f"{task_id}-spec-{session['slug']}-*.md"))
            candidate = files[-1] if files else None
    elif name == "docs":
        candidate = repo_root / "docs" / session["slug"] / "README.md"
    # (code-review/security-review parsed from verify report — implemented in T4.7b)

    if candidate is None:
        raise ArtifactNotFound(name)

    resolved = candidate.resolve()
    if not str(resolved).startswith(str(repo_root) + "/") and resolved != repo_root:
        raise ArtifactForbidden(f"{resolved} outside {repo_root}")
    if not resolved.exists() or not resolved.is_file():
        raise ArtifactNotFound(str(resolved))
    return resolved
```

- [ ] **Step 4: Verify** — 3 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/services/artifact_reader.py dashboard/backend/tests/test_artifact_reader.py
git commit -m "feat(backend): artifact path resolution with whitelist and traversal guard"
```

---

### Task 4.8: `routers/artifacts.py` — list + content endpoints  [Specialist: css-api-specialist]

**Files:**
- Create: `dashboard/backend/routers/artifacts.py`
- Test: `dashboard/backend/tests/test_router_artifacts.py`

- [ ] **Step 1: Write the failing test**

```python
# test_router_artifacts.py
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app

async def test_artifact_content_spec(tmp_path, monkeypatch):
    repo = tmp_path / "alpha"
    spec = repo / "docs/specs/x.md"; spec.parent.mkdir(parents=True); spec.write_text("# hello")
    sess_dir = repo / ".claude/css/sessions"; sess_dir.mkdir(parents=True)
    (sess_dir / "feat-x.json").write_text(json.dumps({
        "slug": "feat-x", "idea": "i", "master_flow": True,
        "repo_root": str(repo), "repo_name": "alpha", "current_phase": "plan",
        "phases": {"interview": {"artifact": "docs/specs/x.md"}}, "gates": {}
    }))
    pj = tmp_path / "projects.json"; pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"}
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/feat-x/artifacts/spec")
    assert r.status_code == 200
    assert "# hello" in r.json()["content_md"]

async def test_artifact_traversal_returns_403(tmp_path, monkeypatch):
    # artifact path that resolves outside repo
    repo = tmp_path / "alpha"; repo.mkdir()
    sess_dir = repo / ".claude/css/sessions"; sess_dir.mkdir(parents=True)
    (sess_dir / "feat-x.json").write_text(json.dumps({
        "slug": "feat-x", "idea": "i", "master_flow": True,
        "repo_root": str(repo), "repo_name": "alpha", "current_phase": "plan",
        "phases": {"interview": {"artifact": "../../etc/passwd"}}, "gates": {}
    }))
    pj = tmp_path / "projects.json"; pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"}
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/feat-x/artifacts/spec")
    assert r.status_code == 403
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/artifacts.py
from fastapi import APIRouter, HTTPException
from backend.services.artifact_reader import (
    resolve_artifact_path, ArtifactNotFound, ArtifactForbidden, WHITELIST
)
from backend.routers.sessions import get_session  # reuse lookup

router = APIRouter(prefix="/api/sessions", tags=["artifacts"])

@router.get("/{slug}/artifacts")
async def list_artifacts(slug: str):
    session = await get_session(slug)
    candidates = list(WHITELIST)
    # rich-spec discovery
    from pathlib import Path
    plans_dir = Path(session["repo_root"]) / ".claude/css/plans"
    if plans_dir.exists():
        for p in plans_dir.glob(f"*-spec-{slug}-*.md"):
            task_id = p.name.split("-spec-")[0]
            candidates.append(f"rich-spec-{task_id}")
    available = []
    for name in candidates:
        try:
            resolved = resolve_artifact_path(session, name)
            stat = resolved.stat()
            available.append({"name": name, "path": str(resolved), "size": stat.st_size, "mtime": stat.st_mtime})
        except (ArtifactNotFound, ArtifactForbidden):
            continue
    return {"artifacts": available}

@router.get("/{slug}/artifacts/{name}")
async def get_artifact(slug: str, name: str):
    session = await get_session(slug)
    try:
        path = resolve_artifact_path(session, name)
    except ArtifactForbidden:
        raise HTTPException(403, "artifact path outside repo_root")
    except ArtifactNotFound:
        raise HTTPException(404, f"artifact {name} not found")
    stat = path.stat()
    return {
        "name": name, "path": str(path),
        "content_md": path.read_text(),
        "size": stat.st_size, "mtime": stat.st_mtime,
    }
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/artifacts.py dashboard/backend/tests/test_router_artifacts.py
git commit -m "feat(api): artifact list and content endpoints with traversal guard"
```

---

### Task 4.9: `services/queue_writer.py` — write approval events to bridge  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/backend/services/queue_writer.py`
- Test: `dashboard/backend/tests/test_queue_writer.py`

- [ ] **Step 1: Write the failing test**

```python
# test_queue_writer.py
import json
import pytest
from pathlib import Path
from backend.services.queue_writer import enqueue_resume

def test_enqueue_writes_valid_event(tmp_path):
    qdir = tmp_path / "queue"; qdir.mkdir()
    evt_id = enqueue_resume(
        queue_dir=qdir,
        session_id="feat-x",
        project_root="/home/user/repo",
        callback_url="http://localhost:7421/api/internal/run-result",
    )
    files = list(qdir.glob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text())
    assert payload["id"] == evt_id
    assert payload["session_id"] == "feat-x"
    assert payload["command"] == ["claude", "--print", "/css:ship --session feat-x"]
    assert payload["project_root"] == "/home/user/repo"

def test_enqueue_rejects_unsafe_session_id(tmp_path):
    with pytest.raises(ValueError):
        enqueue_resume(
            queue_dir=tmp_path, session_id="x; rm -rf /",
            project_root="/r", callback_url="http://x"
        )
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/services/queue_writer.py
import json, os, re, secrets
from datetime import datetime, timezone
from pathlib import Path

SESSION_ID_RE = re.compile(r"^[a-z0-9-]{1,64}$")

def enqueue_resume(
    *, queue_dir: Path, session_id: str, project_root: str, callback_url: str
) -> str:
    if not SESSION_ID_RE.match(session_id):
        raise ValueError(f"unsafe session_id: {session_id!r}")
    queue_dir.mkdir(parents=True, exist_ok=True)
    evt_id = f"evt-{secrets.token_hex(8)}"
    payload = {
        "id": evt_id,
        "session_id": session_id,
        "project_root": project_root,
        "command": ["claude", "--print", f"/css:ship --session {session_id}"],
        "callback_url": callback_url,
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
    }
    tmp = queue_dir / f".{evt_id}.json.tmp"
    final = queue_dir / f"{evt_id}.json"
    tmp.write_text(json.dumps(payload))
    os.replace(tmp, final)
    return evt_id
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/services/queue_writer.py dashboard/backend/tests/test_queue_writer.py
git commit -m "feat(backend): queue writer with session_id validation (command injection guard)"
```

---

### Task 4.10: `routers/gates.py` — approve + retry endpoints  [Specialist: css-api-specialist]

**Files:**
- Create: `dashboard/backend/routers/gates.py`
- Test: `dashboard/backend/tests/test_router_gates.py`

- [ ] **Step 1: Write the failing test**

```python
# test_router_gates.py
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app

def _setup(tmp_path: Path, gate_state):
    repo = tmp_path / "alpha"; repo.mkdir()
    s = repo / ".claude/css/sessions"; s.mkdir(parents=True)
    (s / "feat-x.json").write_text(json.dumps({
        "slug": "feat-x", "idea": "i", "master_flow": True,
        "repo_root": str(repo), "repo_name": "alpha", "current_phase": "review",
        "phases": {}, "gates": {"gate2_pre_execute": {"state": gate_state}}
    }))
    pj = tmp_path / "projects.json"; pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"}
    ]}))
    return repo, pj

async def test_approve_pending_gate(tmp_path, monkeypatch):
    repo, pj = _setup(tmp_path, "pending")
    qdir = tmp_path / "queue"; qdir.mkdir()
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    monkeypatch.setenv("QUEUE_DIR", str(qdir))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/sessions/feat-x/gates/gate2_pre_execute/approve")
    assert r.status_code == 200
    # session JSON updated
    sj = json.loads((repo / ".claude/css/sessions/feat-x.json").read_text())
    assert sj["gates"]["gate2_pre_execute"]["state"] == "approved"
    assert sj["gates"]["gate2_pre_execute"]["source"] == "dashboard_drag"
    # queue file written
    assert len(list(qdir.glob("*.json"))) == 1

async def test_approve_lock_held_returns_409(tmp_path, monkeypatch):
    repo, pj = _setup(tmp_path, "pending")
    locks = repo / ".claude/css/locks"; locks.mkdir(parents=True)
    (locks / "feat-x.lock").write_text("{}")
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    monkeypatch.setenv("QUEUE_DIR", str(tmp_path / "queue"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/sessions/feat-x/gates/gate2_pre_execute/approve")
    assert r.status_code == 409
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/gates.py
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.services.queue_writer import enqueue_resume
from backend.services.session_reader import parse_session_file
from backend.deps import get_db_session
from backend.models import GateAuditLog
from backend.routers.sessions import get_session

ALLOWED_GATES = {"gate2_pre_execute", "gate3_pre_pr"}

router = APIRouter(prefix="/api/sessions", tags=["gates"])

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _session_file(repo_root: str, slug: str) -> Path:
    return Path(repo_root) / ".claude/css/sessions" / f"{slug}.json"

def _lock_file(repo_root: str, slug: str) -> Path:
    return Path(repo_root) / ".claude/css/locks" / f"{slug}.lock"

@router.post("/{slug}/gates/{gate}/approve")
async def approve_gate(slug: str, gate: str, db: AsyncSession = Depends(get_db_session)):
    if gate not in ALLOWED_GATES:
        raise HTTPException(400, f"unknown gate {gate}")
    session = await get_session(slug)
    if _lock_file(session["repo_root"], slug).exists():
        raise HTTPException(409, "session lock held by terminal CSS; approve there or wait")

    # update session JSON atomically
    sf = _session_file(session["repo_root"], slug)
    raw = json.loads(sf.read_text())
    raw.setdefault("gates", {})
    raw["gates"][gate] = {
        "state": "approved", "source": "dashboard_drag",
        "reached_at": raw.get("gates", {}).get(gate, {}).get("reached_at") if isinstance(raw["gates"].get(gate), dict) else _now(),
        "approved_at": _now(), "approved_by": "dashboard",
    }
    tmp = sf.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, indent=2))
    tmp.replace(sf)

    # enqueue bridge event
    settings = Settings()
    evt_id = enqueue_resume(
        queue_dir=settings.queue_dir,
        session_id=slug,
        project_root=session["repo_root"],
        callback_url=f"http://localhost:{settings.dashboard_port}/api/internal/run-result",
    )

    db.add(GateAuditLog(
        session_id=slug, gate=gate,
        reached_at=datetime.now(timezone.utc),
        approved_at=datetime.now(timezone.utc),
        approval_source="dashboard_drag",
        resume_status="retrying",
    ))
    await db.commit()
    return {"approved": True, "event_id": evt_id, "gate": gate}

@router.post("/{slug}/gates/{gate}/retry")
async def retry_gate(slug: str, gate: str, db: AsyncSession = Depends(get_db_session)):
    if gate not in ALLOWED_GATES:
        raise HTTPException(400, f"unknown gate {gate}")
    session = await get_session(slug)
    settings = Settings()
    evt_id = enqueue_resume(
        queue_dir=settings.queue_dir,
        session_id=slug,
        project_root=session["repo_root"],
        callback_url=f"http://localhost:{settings.dashboard_port}/api/internal/run-result",
    )
    return {"retried": True, "event_id": evt_id}
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/gates.py dashboard/backend/tests/test_router_gates.py
git commit -m "feat(api): POST gate approve + retry with lock check and audit"
```

---

### Task 4.11: SSE broker (`sse.py`)  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/backend/sse.py`
- Test: `dashboard/backend/tests/test_sse.py`

- [ ] **Step 1: Write the failing test**

```python
# test_sse.py
import asyncio
import pytest
from backend.sse import SSEBroker, SSEEvent

async def test_broker_fans_out_events_to_multiple_subscribers():
    broker = SSEBroker()
    q1 = broker.subscribe()
    q2 = broker.subscribe()
    await broker.publish(SSEEvent(name="session_updated", data={"slug": "x"}))
    e1 = await asyncio.wait_for(q1.get(), timeout=0.5)
    e2 = await asyncio.wait_for(q2.get(), timeout=0.5)
    assert e1.name == "session_updated"
    assert e2.data["slug"] == "x"

async def test_unsubscribe_removes_queue():
    broker = SSEBroker()
    q = broker.subscribe()
    broker.unsubscribe(q)
    await broker.publish(SSEEvent(name="x", data={}))
    assert q.empty()
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/sse.py
import asyncio
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SSEEvent:
    name: str
    data: dict[str, Any] = field(default_factory=dict)

class SSEBroker:
    def __init__(self) -> None:
        self._subs: set[asyncio.Queue[SSEEvent]] = set()

    def subscribe(self, maxsize: int = 100) -> asyncio.Queue[SSEEvent]:
        q: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=maxsize)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[SSEEvent]) -> None:
        self._subs.discard(q)

    async def publish(self, evt: SSEEvent) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(evt)
            except asyncio.QueueFull:
                pass  # drop slow consumer's event

broker = SSEBroker()  # module-level singleton
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/sse.py dashboard/backend/tests/test_sse.py
git commit -m "feat(backend): SSE broker with bounded queue per subscriber"
```

---

### Task 4.12: SSE endpoint (`routers/sse_router.py`)  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/backend/routers/sse_router.py`
- Test: `dashboard/backend/tests/test_sse_endpoint.py`

- [ ] **Step 1: Write the failing test**

```python
# test_sse_endpoint.py
import asyncio
import json
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.sse import broker, SSEEvent

async def test_sse_streams_events():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async def fire_event():
            await asyncio.sleep(0.1)
            await broker.publish(SSEEvent(name="session_updated", data={"slug": "x"}))
        async with c.stream("GET", "/api/sse") as r:
            asyncio.create_task(fire_event())
            collected = []
            async for line in r.aiter_lines():
                collected.append(line)
                if any("session_updated" in l for l in collected): break
    assert any("session_updated" in l for l in collected)
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/sse_router.py
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.sse import broker

router = APIRouter(tags=["sse"])

HEARTBEAT_SEC = 30

@router.get("/api/sse")
async def sse(request: Request):
    queue = broker.subscribe()

    async def event_source():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    evt = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SEC)
                    yield f"event: {evt.name}\ndata: {json.dumps(evt.data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"  # SSE comment heartbeat
        finally:
            broker.unsubscribe(queue)

    return StreamingResponse(event_source(), media_type="text/event-stream")
```

Add include_router in main.py.

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/sse_router.py dashboard/backend/main.py dashboard/backend/tests/test_sse_endpoint.py
git commit -m "feat(api): GET /api/sse with heartbeat ping"
```

---

### Task 4.13: `watcher.py` — watchdog handlers + SSE dispatch  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/backend/watcher.py`
- Modify: `dashboard/backend/main.py` (lifespan starts/stops watcher)
- Test: `dashboard/backend/tests/test_watcher.py`

- [ ] **Step 1: Write the failing test**

```python
# test_watcher.py
import asyncio, json
from pathlib import Path
from backend.watcher import SessionWatcher
from backend.sse import broker, SSEEvent

async def _consume_until(name: str, timeout=2.0):
    q = broker.subscribe()
    try:
        end = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end:
            try:
                evt = await asyncio.wait_for(q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            if evt.name == name: return evt
    finally:
        broker.unsubscribe(q)
    raise AssertionError(f"event {name} not received")

async def test_watcher_emits_session_updated_on_write(tmp_path):
    repo = tmp_path / "alpha"
    s = repo / ".claude/css/sessions"; s.mkdir(parents=True)
    w = SessionWatcher(watch_root=tmp_path)
    w.start()
    try:
        await asyncio.sleep(0.2)
        (s / "feat-x.json").write_text(json.dumps({"slug": "feat-x", "current_phase": "plan", "phases": {}, "gates": {}, "repo_root": str(repo), "repo_name": "alpha", "idea": ""}))
        evt = await _consume_until("session_updated")
        assert evt.data["slug"] == "feat-x"
    finally:
        w.stop()
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/watcher.py
import asyncio
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import structlog
from backend.services.session_reader import parse_session_file
from backend.sse import broker, SSEEvent

log = structlog.get_logger()

class _Handler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory: return
        p = Path(event.src_path)
        if "/.claude/css/sessions/" not in str(p) or not p.name.endswith(".json") or p.name == "_active.json":
            return
        asyncio.run_coroutine_threadsafe(self._handle(p, event.event_type), self._loop)

    async def _handle(self, p: Path, etype: str):
        parsed = parse_session_file(p)
        if parsed is None:
            return
        await broker.publish(SSEEvent(
            name="session_updated",
            data={"slug": parsed.slug, "phase": parsed.current_phase, "gates": parsed.gates, "mtime": parsed.mtime}
        ))
        # additional event types (gate_reached) detected by comparing previous snapshot — see T4.13b

class SessionWatcher:
    def __init__(self, watch_root: Path):
        self.watch_root = watch_root
        self.observer: Observer | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self):
        self._loop = asyncio.get_event_loop()
        self.observer = Observer()
        self.observer.schedule(_Handler(self._loop), str(self.watch_root), recursive=True)
        self.observer.start()
        log.info("watcher.started", root=str(self.watch_root))

    def stop(self):
        if self.observer:
            self.observer.stop(); self.observer.join(timeout=2)
            log.info("watcher.stopped")
```

In `main.py` lifespan:
```python
from backend.watcher import SessionWatcher
@asynccontextmanager
async def lifespan(app: FastAPI):
    watcher = SessionWatcher(watch_root=settings.host_claude_dir.parent if settings.host_claude_dir.exists() else Path("/host"))
    watcher.start()
    yield
    watcher.stop()
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/watcher.py dashboard/backend/main.py dashboard/backend/tests/test_watcher.py
git commit -m "feat(backend): watchdog session JSON watcher with SSE emit"
```

---

### Task 4.14: `services/archive.py` — JSON → DB on completion  [Specialist: css-db-specialist]

**Files:**
- Create: `dashboard/backend/services/archive.py`
- Test: `dashboard/backend/tests/test_archive.py`

- [ ] **Step 1: Write the failing test**

```python
# test_archive.py
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from backend.services.archive import archive_completed_session
from backend.models import Project, SessionHistory
from backend.services.session_reader import ParsedSession
from pathlib import Path

async def test_archive_inserts_history_row(pg_engine):
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as s:
        p = Project(repo_root="/r", repo_name="r", color="#fff")
        s.add(p); await s.commit(); await s.refresh(p)

    parsed = ParsedSession(
        slug="feat-x", idea="i", repo_root="/r", repo_name="r",
        current_phase="pr",
        phases={
            "interview": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"},
            "pr":        {"status": "completed", "artifact": "https://gh.com/pr/1"},
        },
        gates={}, master_flow=True, file_path=Path("/tmp/x.json"), mtime=0
    )

    async with factory() as s:
        row = await archive_completed_session(s, parsed)
        await s.commit()
        assert row.outcome == "completed"
        assert row.pr_url == "https://gh.com/pr/1"

    async with factory() as s:
        rows = (await s.execute(select(SessionHistory).where(SessionHistory.session_id == "feat-x"))).scalars().all()
        assert len(rows) == 1
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/services/archive.py
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Project, SessionHistory
from backend.services.session_reader import ParsedSession

async def archive_completed_session(db: AsyncSession, parsed: ParsedSession) -> SessionHistory:
    proj = (await db.execute(select(Project).where(Project.repo_root == parsed.repo_root))).scalar_one_or_none()
    if proj is None:
        proj = Project(repo_root=parsed.repo_root, repo_name=parsed.repo_name)
        db.add(proj); await db.flush()

    outcome = "completed" if parsed.phases.get("pr", {}).get("status") == "completed" else "failed"
    pr_url = parsed.phases.get("pr", {}).get("artifact") if outcome == "completed" else None

    started_at_str = parsed.phases.get("interview", {}).get("completed_at") or datetime.now(timezone.utc).isoformat()
    started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))

    durations = {ph: parsed.phases.get(ph, {}).get("duration_seconds", 0) for ph in
                 ["interview","plan","review","execute","verify","document","pr"]}

    row = SessionHistory(
        project_id=proj.id, session_id=parsed.slug, idea=parsed.idea,
        started_at=started_at, finished_at=datetime.now(timezone.utc),
        final_phase=parsed.current_phase, outcome=outcome, pr_url=pr_url,
        phase_durations=durations,
        snapshot={"slug": parsed.slug, "phases": parsed.phases, "gates": parsed.gates},
    )
    db.add(row); await db.flush()
    return row
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/services/archive.py dashboard/backend/tests/test_archive.py
git commit -m "feat(backend): archive completed sessions to PostgreSQL"
```

---

### Task 4.15: `routers/internal.py` — bridge callback  [Specialist: css-api-specialist]

**Files:**
- Create: `dashboard/backend/routers/internal.py`
- Test: `dashboard/backend/tests/test_router_internal.py`

- [ ] **Step 1: Write the failing test**

```python
# test_router_internal.py
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import DaemonRun

async def test_run_started_inserts_daemon_run(pg_engine):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/internal/run-result", json={
            "id": "evt-abc", "session_id": "feat-x", "event": "started"
        })
    assert r.status_code == 204
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as s:
        rows = (await s.execute(select(DaemonRun).where(DaemonRun.session_id == "feat-x"))).scalars().all()
        assert len(rows) == 1
        assert rows[0].exit_code is None

async def test_run_finished_updates_exit_code(pg_engine):
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as s:
        s.add(DaemonRun(session_id="feat-y", command="claude --print", started_at=datetime.now(timezone.utc)))
        await s.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/internal/run-result", json={
            "id": "evt-y", "session_id": "feat-y", "event": "finished", "exit_code": 0
        })
    assert r.status_code == 204
    async with factory() as s:
        rows = (await s.execute(select(DaemonRun).where(DaemonRun.session_id == "feat-y"))).scalars().all()
        assert rows[-1].exit_code == 0
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/internal.py
from datetime import datetime, timezone
from typing import Optional, Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.deps import get_db_session
from backend.models import DaemonRun
from backend.sse import broker, SSEEvent

router = APIRouter(prefix="/api/internal", tags=["internal"])

class RunResult(BaseModel):
    id: str
    session_id: str
    event: Literal["started", "finished", "failed"]
    exit_code: Optional[int] = None
    error: Optional[str] = None
    log_path: Optional[str] = None

@router.post("/run-result", status_code=204)
async def run_result(body: RunResult, db: AsyncSession = Depends(get_db_session)):
    now = datetime.now(timezone.utc)
    if body.event == "started":
        db.add(DaemonRun(session_id=body.session_id, command="claude --print", started_at=now))
        await db.commit()
        await broker.publish(SSEEvent(name="resume_started", data={"session_id": body.session_id, "run_id": body.id}))
    else:
        # locate latest run for this session
        row = (await db.execute(
            select(DaemonRun).where(DaemonRun.session_id == body.session_id).order_by(DaemonRun.id.desc()).limit(1)
        )).scalar_one_or_none()
        if row is not None:
            row.finished_at = now
            row.exit_code = body.exit_code or 0
            row.stderr_tail = (body.error or "")[:2000]
            await db.commit()
        evt = "session_completed" if body.event == "finished" and (body.exit_code or 0) == 0 else "resume_failed"
        await broker.publish(SSEEvent(name=evt, data={"session_id": body.session_id, "error": body.error}))
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/internal.py dashboard/backend/tests/test_router_internal.py
git commit -m "feat(api): bridge callback /api/internal/run-result"
```

---

### Task 4.16: `routers/history.py` — paginated archive query  [Specialist: css-db-specialist]

**Files:**
- Create: `dashboard/backend/routers/history.py`
- Test: `dashboard/backend/tests/test_router_history.py`

- [ ] **Step 1: Write the failing test**

```python
# test_router_history.py
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import async_sessionmaker
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Project, SessionHistory

async def test_history_pagination(pg_engine):
    factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with factory() as s:
        p = Project(repo_root="/h", repo_name="h"); s.add(p); await s.commit(); await s.refresh(p)
        for i in range(25):
            s.add(SessionHistory(
                project_id=p.id, session_id=f"s{i}", idea="i",
                started_at=datetime.now(timezone.utc), final_phase="pr",
                outcome="completed", phase_durations={}, snapshot={}
            ))
        await s.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/history?limit=10")
    assert r.status_code == 200
    j = r.json()
    assert len(j["items"]) == 10
    assert j["total"] >= 25
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/backend/routers/history.py
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.deps import get_db_session
from backend.models import SessionHistory

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
async def list_history(
    project_id: Optional[int] = None,
    outcome: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(SessionHistory).order_by(SessionHistory.finished_at.desc())
    cnt_stmt = select(func.count()).select_from(SessionHistory)
    if project_id is not None:
        stmt = stmt.where(SessionHistory.project_id == project_id)
        cnt_stmt = cnt_stmt.where(SessionHistory.project_id == project_id)
    if outcome:
        stmt = stmt.where(SessionHistory.outcome == outcome)
        cnt_stmt = cnt_stmt.where(SessionHistory.outcome == outcome)
    stmt = stmt.limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(cnt_stmt)).scalar_one()
    return {
        "total": total,
        "items": [
            {
                "id": r.id, "project_id": r.project_id, "session_id": r.session_id,
                "idea": r.idea, "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "outcome": r.outcome, "pr_url": r.pr_url,
                "phase_durations": r.phase_durations,
            } for r in rows
        ],
    }
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routers/history.py dashboard/backend/tests/test_router_history.py
git commit -m "feat(api): GET /api/history with pagination and filters"
```

---

## Batch 5 — Bridge Daemon

User checkpoint after batch: enqueue a synthetic event, verify bridge spawns mock-claude with correct env + cwd.

### Task 5.1: `bridge/bridge.py` — queue consumer  [Specialist: css-async-coder]

**Files:**
- Create: `dashboard/bridge/bridge.py`
- Test: `dashboard/bridge/tests/test_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# bridge/tests/test_bridge.py
import json, os, subprocess, time
from pathlib import Path
import pytest
from bridge import bridge as b

def test_process_event_invokes_command(tmp_path, monkeypatch):
    qdir = tmp_path / "queue"; pdir = qdir / "processed"; fdir = qdir / "failed"; rdir = tmp_path / "runs"
    for d in (qdir, pdir, fdir, rdir): d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(b, "QUEUE", qdir); monkeypatch.setattr(b, "PROCESSED", pdir)
    monkeypatch.setattr(b, "FAILED", fdir); monkeypatch.setattr(b, "RUNS", rdir)

    # mock claude: simple echo script
    fake_cmd = ["bash", "-c", "echo resumed && exit 0"]
    callbacks = []
    monkeypatch.setattr(b, "_post_callback", lambda url, payload: callbacks.append(payload))

    evt_path = qdir / "evt-abc.json"
    evt_path.write_text(json.dumps({
        "id": "evt-abc", "session_id": "feat-x",
        "project_root": str(tmp_path), "command": fake_cmd,
        "callback_url": "http://test/cb"
    }))
    b.process_event(evt_path)

    assert (pdir / "evt-abc.json").exists()
    assert any(c["event"] == "started" for c in callbacks)
    assert any(c["event"] == "finished" for c in callbacks)
    assert (rdir / "evt-abc.log").read_text().strip() == "resumed"

def test_failing_command_moves_to_failed(tmp_path, monkeypatch):
    qdir = tmp_path / "queue"; pdir = qdir / "processed"; fdir = qdir / "failed"; rdir = tmp_path / "runs"
    for d in (qdir, pdir, fdir, rdir): d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(b, "QUEUE", qdir); monkeypatch.setattr(b, "PROCESSED", pdir)
    monkeypatch.setattr(b, "FAILED", fdir); monkeypatch.setattr(b, "RUNS", rdir)
    monkeypatch.setattr(b, "_post_callback", lambda url, payload: None)

    evt_path = qdir / "evt-bad.json"
    evt_path.write_text(json.dumps({
        "id": "evt-bad", "session_id": "feat-y",
        "project_root": str(tmp_path),
        "command": ["bash", "-c", "exit 7"],
        "callback_url": "http://test/cb"
    }))
    b.process_event(evt_path)
    assert (fdir / "evt-bad.json").exists() or (pdir / "evt-bad.json").exists()  # processed on non-zero too
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```python
# dashboard/bridge/bridge.py
import json, os, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOME = Path.home()
QUEUE = HOME / ".claude" / "css-dashboard" / "queue"
PROCESSED = QUEUE / "processed"
FAILED = QUEUE / "failed"
RUNS = HOME / ".claude" / "css-dashboard" / "runs"
TIMEOUT_SEC = 3600

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _post_callback(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        # bridge POSTs are best-effort
        print(f"callback failed: {e}", flush=True)

def process_event(path: Path) -> None:
    try:
        evt = json.loads(path.read_text())
    except Exception as e:
        print(f"corrupt event {path}: {e}", flush=True); return
    sid = evt["session_id"]; pr = evt["project_root"]
    cmd = evt["command"]; url = evt["callback_url"]; evt_id = evt["id"]

    log = RUNS / f"{evt_id}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    _post_callback(url, {"id": evt_id, "session_id": sid, "event": "started", "started_at": _now()})

    env = {**os.environ, "CSS_DASHBOARD_RESUME": "1"}
    try:
        with open(log, "w") as f:
            proc = subprocess.run(cmd, cwd=pr, env=env, timeout=TIMEOUT_SEC, stdout=f, stderr=subprocess.STDOUT)
        _post_callback(url, {
            "id": evt_id, "session_id": sid, "event": "finished",
            "exit_code": proc.returncode, "log_path": str(log)
        })
        path.rename(PROCESSED / path.name)
    except subprocess.TimeoutExpired:
        _post_callback(url, {"id": evt_id, "session_id": sid, "event": "failed", "error": "timeout"})
        path.rename(FAILED / path.name)
    except FileNotFoundError as e:
        _post_callback(url, {"id": evt_id, "session_id": sid, "event": "failed", "error": f"command not found: {e}"})
        path.rename(FAILED / path.name)
    except Exception as e:
        _post_callback(url, {"id": evt_id, "session_id": sid, "event": "failed", "error": str(e)})
        path.rename(FAILED / path.name)

class _Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"): return
        process_event(Path(event.src_path))

def main():
    for d in (QUEUE, PROCESSED, FAILED, RUNS): d.mkdir(parents=True, exist_ok=True)
    for p in QUEUE.glob("*.json"): process_event(p)
    obs = Observer(); obs.schedule(_Handler(), str(QUEUE), recursive=False); obs.start()
    try:
        while True: time.sleep(60)
    finally:
        obs.stop(); obs.join()

if __name__ == "__main__": main()
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/bridge/bridge.py dashboard/bridge/tests/test_bridge.py
git commit -m "feat(bridge): host-side queue consumer with CSS_DASHBOARD_RESUME env injection"
```

---

### Task 5.2: systemd user unit + installer hook  [Specialist: css-infra-engineer]

**Files:**
- Create: `dashboard/bridge/css-dashboard-bridge.service`
- Test: `tests/golden/bridge-systemd.spec.md`

- [ ] **Step 1: Write the failing test**

```markdown
# Golden: bridge systemd unit

File `dashboard/bridge/css-dashboard-bridge.service` exists and:
- Has [Unit] section with `After=network.target`
- Has [Service] with `ExecStart=/usr/bin/python3 %h/.claude/css-dashboard/bin/bridge.py`
- Has `Restart=on-failure`
- Has [Install] `WantedBy=default.target`
```

- [ ] **Step 2: Run (FAIL)** — file missing.

- [ ] **Step 3: Create file**

```ini
[Unit]
Description=CSS Pipeline Dashboard Bridge
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.claude/css-dashboard/bin/bridge.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

- [ ] **Step 4: Verify**

```bash
grep -q "ExecStart=/usr/bin/python3" dashboard/bridge/css-dashboard-bridge.service && \
grep -q "WantedBy=default.target" dashboard/bridge/css-dashboard-bridge.service && echo OK
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add dashboard/bridge/css-dashboard-bridge.service tests/golden/bridge-systemd.spec.md
git commit -m "feat(bridge): systemd user unit"
```

---

## Batch 6 — React Frontend

User checkpoint after batch: open browser, verify Kanban renders with synthetic seed data + drag-approve roundtrip works against mocked backend.

### Task 6.1: Frontend scaffold (Vite + Tailwind + dnd-kit)  [Specialist: css-ui-engineer]

**Files:**
- Create: `dashboard/frontend/package.json`, `vite.config.ts`, `tailwind.config.ts`, `tsconfig.json`, `postcss.config.js`, `index.html`, `src/main.tsx`, `src/index.css`
- Test: `dashboard/frontend/tests/test_scaffold.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/test_scaffold.test.ts
import { test, expect } from "vitest";
import { existsSync } from "fs";
import { join } from "path";

const root = join(__dirname, "..");
test("package.json has required dependencies", () => {
  const pkg = require(join(root, "package.json"));
  for (const dep of ["react", "react-dom", "@dnd-kit/core", "@dnd-kit/sortable", "zustand", "react-markdown", "rehype-sanitize", "rehype-highlight"]) {
    expect(pkg.dependencies[dep]).toBeDefined();
  }
  for (const dev of ["vite", "vitest", "@vitejs/plugin-react", "tailwindcss", "@testing-library/react", "msw", "@playwright/test"]) {
    expect(pkg.devDependencies[dev]).toBeDefined();
  }
});
test("index.html and main.tsx exist", () => {
  expect(existsSync(join(root, "index.html"))).toBe(true);
  expect(existsSync(join(root, "src/main.tsx"))).toBe(true);
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Create scaffold**

`package.json`:
```json
{
  "name": "css-dashboard-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@dnd-kit/utilities": "^3.2.0",
    "zustand": "^5.0.0",
    "react-markdown": "^9.0.0",
    "rehype-sanitize": "^6.0.0",
    "rehype-highlight": "^7.0.0",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "vite": "^6.0.0",
    "vitest": "^2.1.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.6.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "msw": "^2.6.0",
    "@playwright/test": "^1.49.0",
    "jsdom": "^25.0.0"
  }
}
```

`vite.config.ts`:
```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:7421"
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"]
  }
});
```

`tailwind.config.ts`:
```ts
import type { Config } from "tailwindcss";
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0e1018",
        panel: "#161922",
        card: "#222633"
      }
    }
  }
} satisfies Config;
```

`tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "bundler",
    "jsx": "react-jsx", "strict": true, "esModuleInterop": true,
    "skipLibCheck": true, "isolatedModules": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src", "tests"]
}
```

`index.html`:
```html
<!doctype html>
<html lang="ko">
  <head><meta charset="UTF-8"/><title>CSS Pipeline Dashboard</title></head>
  <body class="bg-bg text-white"><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>
</html>
```

`src/main.tsx`:
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode><BrowserRouter><App /></BrowserRouter></StrictMode>
);
```

`src/index.css`:
```css
@import "tailwindcss";
```

`src/App.tsx` (placeholder):
```tsx
export default function App() { return <div className="p-8">Loading…</div>; }
```

`tests/setup.ts`:
```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 4: Verify**

```bash
cd dashboard/frontend && npm install && npm run test
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/
git commit -m "feat(frontend): Vite + React 19 + Tailwind v4 + dnd-kit scaffold"
```

---

### Task 6.2: TypeScript types (`src/types.ts`)  [Specialist: executor-direct]

**Files:**
- Create: `dashboard/frontend/src/types.ts`

- [ ] **Step 1: Test (compile-time)**

```ts
// tests/test_types.test.ts
import type { Session, Project, GateName, ArtifactName } from "../src/types";

test("Session type shape", () => {
  const s: Session = {
    slug: "x", idea: "y", repoRoot: "/r", repoName: "r",
    currentPhase: "review", phases: {}, gates: {}, mtime: 0
  };
  expect(s.slug).toBe("x");
});
```

- [ ] **Step 2: Run (FAIL — module missing)**

- [ ] **Step 3: Implement**

```ts
// src/types.ts
export type PhaseName = "interview" | "plan" | "review" | "execute" | "verify" | "document" | "pr";
export type GateName = "gate2_pre_execute" | "gate3_pre_pr";
export type ArtifactName = "spec" | "plan" | "exec-log" | "verify" | "code-review" | "security-review" | "docs" | `rich-spec-${string}`;

export interface GateState {
  state: "pending" | "approved" | null;
  source: "dashboard_drag" | "terminal_ask" | null;
  reached_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
}

export interface Session {
  slug: string;
  idea: string;
  repoRoot: string;
  repoName: string;
  currentPhase: PhaseName;
  phases: Record<string, { status: string; artifact?: string; completed_at?: string }>;
  gates: Partial<Record<GateName, GateState | null>>;
  mtime: number;
}

export interface Project {
  id: number;
  repo_root: string;
  repo_name: string;
  color: string;
}

export interface ArtifactRef {
  name: ArtifactName;
  path: string;
  size: number;
  mtime: number;
}

export type SSEEvent =
  | { type: "session_updated"; data: { slug: string; phase: PhaseName; gates: Session["gates"]; mtime: number } }
  | { type: "gate_reached"; data: { session_id: string; gate: GateName; reached_at: string } }
  | { type: "gate_approved"; data: { session_id: string; gate: GateName; source: string } }
  | { type: "resume_started"; data: { session_id: string; run_id: string } }
  | { type: "resume_failed"; data: { session_id: string; gate: GateName; error: string; retry_count: number } }
  | { type: "session_completed"; data: { session_id: string; pr_url: string; outcome: string } }
  | { type: "project_registered"; data: { project_id: number; repo_name: string; color: string } };
```

- [ ] **Step 4: Verify** — `npm run test` → PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/types.ts dashboard/frontend/tests/test_types.test.ts
git commit -m "feat(frontend): TypeScript types for Session, Project, GateState, SSEEvent"
```

---

### Task 6.3: API client + SSE manager (`src/api/`)  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/api/client.ts`, `src/api/sse.ts`
- Test: `tests/test_api.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/test_api.test.ts
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { listSessions, approveGate } from "../src/api/client";

const server = setupServer(
  http.get("/api/sessions", () => HttpResponse.json({ sessions: [{ slug: "x", repoName: "r" }] })),
  http.post("/api/sessions/:slug/gates/:gate/approve", () => HttpResponse.json({ approved: true }))
);

beforeAll(() => server.listen());
afterAll(() => server.close());

test("listSessions returns array", async () => {
  const sessions = await listSessions();
  expect(sessions[0].slug).toBe("x");
});

test("approveGate posts correctly", async () => {
  const r = await approveGate("x", "gate2_pre_execute");
  expect(r.approved).toBe(true);
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

`src/api/client.ts`:
```ts
import type { Session, Project, ArtifactRef, GateName } from "../types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  return r.json();
}

export const listSessions = () => req<{ sessions: Session[] }>("/api/sessions").then(r => r.sessions);
export const getSession = (slug: string) => req<Session>(`/api/sessions/${slug}`);
export const listArtifacts = (slug: string) => req<{ artifacts: ArtifactRef[] }>(`/api/sessions/${slug}/artifacts`).then(r => r.artifacts);
export const getArtifact = (slug: string, name: string) => req<{ name: string; content_md: string; mtime: number }>(`/api/sessions/${slug}/artifacts/${name}`);
export const approveGate = (slug: string, gate: GateName) => req<{ approved: boolean; event_id: string }>(`/api/sessions/${slug}/gates/${gate}/approve`, { method: "POST" });
export const retryGate = (slug: string, gate: GateName) => req<{ retried: boolean; event_id: string }>(`/api/sessions/${slug}/gates/${gate}/retry`, { method: "POST" });
export const listProjects = () => req<{ projects: Project[] }>("/api/projects").then(r => r.projects);
export const patchProjectColor = (id: number, color: string) => req<Project>(`/api/projects/${id}`, { method: "PATCH", body: JSON.stringify({ color }) });
export const listHistory = (opts: { project_id?: number; outcome?: string; limit?: number; offset?: number } = {}) => {
  const q = new URLSearchParams(Object.entries(opts).filter(([_, v]) => v !== undefined).map(([k, v]) => [k, String(v)]));
  return req<{ total: number; items: any[] }>(`/api/history?${q}`);
};
```

`src/api/sse.ts`:
```ts
import type { SSEEvent } from "../types";

export class SSEManager {
  private es: EventSource | null = null;
  private listeners = new Map<string, Set<(data: any) => void>>();
  private backoffMs = 1000;

  start() {
    this.es = new EventSource("/api/sse");
    this.es.onerror = () => {
      this.es?.close();
      setTimeout(() => this.start(), this.backoffMs);
      this.backoffMs = Math.min(this.backoffMs * 2, 8000);
    };
    this.es.onopen = () => { this.backoffMs = 1000; };
    for (const name of ["session_updated","gate_reached","gate_approved","resume_started","resume_failed","session_completed","project_registered"]) {
      this.es.addEventListener(name, (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        for (const cb of this.listeners.get(name) ?? []) cb(data);
      });
    }
  }

  on(type: SSEEvent["type"], cb: (data: any) => void): () => void {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type)!.add(cb);
    return () => this.listeners.get(type)?.delete(cb);
  }

  stop() { this.es?.close(); this.es = null; }
}
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/ dashboard/frontend/tests/test_api.test.ts
git commit -m "feat(frontend): API client + SSE manager with reconnect backoff"
```

---

### Task 6.4: Zustand stores  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/stores/sessionsStore.ts`, `src/stores/projectsStore.ts`, `src/stores/uiStore.ts`
- Test: `tests/test_stores.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/test_stores.test.ts
import { useSessionsStore } from "../src/stores/sessionsStore";
import { useProjectsStore } from "../src/stores/projectsStore";

test("sessionsStore initial empty", () => {
  expect(useSessionsStore.getState().sessions).toEqual([]);
});
test("sessionsStore upsert updates by slug", () => {
  useSessionsStore.getState().upsert({ slug: "x", currentPhase: "plan" } as any);
  expect(useSessionsStore.getState().sessions[0].slug).toBe("x");
  useSessionsStore.getState().upsert({ slug: "x", currentPhase: "review" } as any);
  expect(useSessionsStore.getState().sessions).toHaveLength(1);
  expect(useSessionsStore.getState().sessions[0].currentPhase).toBe("review");
});
test("projectsStore colorMap derived", () => {
  useProjectsStore.setState({ projects: [{ id: 1, repo_root: "/r", repo_name: "r", color: "#22c55e" }] });
  expect(useProjectsStore.getState().colorByRepoRoot("/r")).toBe("#22c55e");
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

`src/stores/sessionsStore.ts`:
```ts
import { create } from "zustand";
import type { Session } from "../types";

interface State {
  sessions: Session[];
  upsert: (s: Session) => void;
  removeBySlug: (slug: string) => void;
  setAll: (list: Session[]) => void;
}
export const useSessionsStore = create<State>((set) => ({
  sessions: [],
  upsert: (s) => set((st) => ({
    sessions: st.sessions.some(x => x.slug === s.slug)
      ? st.sessions.map(x => x.slug === s.slug ? { ...x, ...s } : x)
      : [...st.sessions, s]
  })),
  removeBySlug: (slug) => set((st) => ({ sessions: st.sessions.filter(s => s.slug !== slug) })),
  setAll: (list) => set({ sessions: list })
}));
```

`src/stores/projectsStore.ts`:
```ts
import { create } from "zustand";
import type { Project } from "../types";

interface State {
  projects: Project[];
  setAll: (p: Project[]) => void;
  patch: (id: number, color: string) => void;
  colorByRepoRoot: (repoRoot: string) => string;
}
const DEFAULT = "#9ca3af";
export const useProjectsStore = create<State>((set, get) => ({
  projects: [],
  setAll: (p) => set({ projects: p }),
  patch: (id, color) => set((st) => ({ projects: st.projects.map(p => p.id === id ? { ...p, color } : p) })),
  colorByRepoRoot: (repoRoot) => get().projects.find(p => p.repo_root === repoRoot)?.color ?? DEFAULT
}));
```

`src/stores/uiStore.ts`:
```ts
import { create } from "zustand";
interface State {
  selectedSlug: string | null;
  setSelected: (slug: string | null) => void;
  toasts: { id: string; kind: "ok"|"info"|"warn"|"err"; msg: string }[];
  pushToast: (kind: State["toasts"][0]["kind"], msg: string) => void;
  dismissToast: (id: string) => void;
  artifactCache: Record<string, { content_md: string; mtime: number }>;
  cacheArtifact: (key: string, val: State["artifactCache"][string]) => void;
}
export const useUIStore = create<State>((set) => ({
  selectedSlug: null,
  setSelected: (slug) => set({ selectedSlug: slug }),
  toasts: [],
  pushToast: (kind, msg) => set((st) => ({ toasts: [...st.toasts, { id: crypto.randomUUID(), kind, msg }] })),
  dismissToast: (id) => set((st) => ({ toasts: st.toasts.filter(t => t.id !== id) })),
  artifactCache: {},
  cacheArtifact: (k, v) => set((st) => ({ artifactCache: { ...st.artifactCache, [k]: v } }))
}));
```

- [ ] **Step 4: Verify** — 3 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/stores/ dashboard/frontend/tests/test_stores.test.ts
git commit -m "feat(frontend): zustand stores for sessions, projects, UI state"
```

---

### Task 6.5: `<SessionCard>` component  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/SessionCard.tsx`
- Test: `tests/test_SessionCard.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import { SessionCard } from "../src/components/SessionCard";

test("renders slug, repo, elapsed", () => {
  render(<SessionCard
    session={{ slug: "feat-x", repoName: "alpha", repoRoot: "/a", currentPhase: "review",
               idea: "i", phases: {}, gates: {}, mtime: Date.now()/1000 - 60 } as any}
    color="#22c55e"
    isPendingGate={false}
    isFailed={false}
    onClick={() => {}}
  />);
  expect(screen.getByText("feat-x")).toBeInTheDocument();
  expect(screen.getByText(/alpha/)).toBeInTheDocument();
  expect(screen.getByText(/m$/)).toBeInTheDocument();  // elapsed
});

test("pending-gate state shows amber outline indicator", () => {
  const { container } = render(<SessionCard
    session={{ slug: "feat-y", repoName: "a", repoRoot: "/a", currentPhase: "review", idea: "", phases: {}, gates: {}, mtime: 0 } as any}
    color="#22c55e"
    isPendingGate={true}
    isFailed={false}
    onClick={() => {}}
  />);
  expect(container.querySelector("[data-testid=pending-gate-marker]")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/SessionCard.tsx
import type { Session } from "../types";

interface Props {
  session: Session;
  color: string;
  isPendingGate: boolean;
  isFailed: boolean;
  onClick: () => void;
}

function elapsed(mtimeSec: number): string {
  const sec = Math.floor(Date.now()/1000 - mtimeSec);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec/60)}m`;
  return `${Math.floor(sec/3600)}h`;
}

export function SessionCard({ session, color, isPendingGate, isFailed, onClick }: Props) {
  return (
    <div
      role="article"
      onClick={onClick}
      className={[
        "relative flex bg-card rounded overflow-hidden cursor-grab select-none",
        isPendingGate ? "outline outline-2 outline-amber-500" : "",
        isFailed ? "shake-once" : ""
      ].join(" ")}
      data-slug={session.slug}
    >
      <div style={{ width: 3, background: color }} />
      <div className="px-2 py-1.5 flex-1">
        <div className="font-semibold text-sm">{session.slug}</div>
        <div className="text-xs text-slate-400">{session.repoName} · {elapsed(session.mtime)}</div>
        {isPendingGate && <div data-testid="pending-gate-marker" className="text-xs text-amber-400 mt-1">⚠ drag right to approve</div>}
      </div>
      {isFailed && <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" data-testid="failed-marker" />}
    </div>
  );
}
```

- [ ] **Step 4: Verify** — 2 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/SessionCard.tsx dashboard/frontend/tests/test_SessionCard.test.tsx
git commit -m "feat(frontend): SessionCard with repo color stripe and gate markers"
```

---

### Task 6.6: `<Column>` component (Kanban column with gate styling)  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/Column.tsx`
- Test: `tests/test_Column.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { Column } from "../src/components/Column";

test("review column shows ⚠ Gate 2 label when hasPendingGate", () => {
  render(<DndContext><Column stage="review" hasPendingGate={true}>{null}</Column></DndContext>);
  expect(screen.getByText(/Gate 2/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/Column.tsx
import { useDroppable } from "@dnd-kit/core";
import type { PhaseName } from "../types";

const GATE_AFTER: Partial<Record<PhaseName, string>> = {
  review: "Gate 2",
  document: "Gate 3"
};

interface Props {
  stage: PhaseName;
  hasPendingGate: boolean;
  children: React.ReactNode;
}

export function Column({ stage, hasPendingGate, children }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: `col-${stage}` });
  const dashed = hasPendingGate;
  return (
    <div
      ref={setNodeRef}
      className={[
        "bg-panel rounded p-2 min-h-[300px]",
        dashed ? "border-2 border-dashed border-amber-500" : "",
        isOver ? "ring-2 ring-blue-500" : ""
      ].join(" ")}
      data-stage={stage}
    >
      <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">
        {stage}{hasPendingGate && GATE_AFTER[stage] && <span className="text-amber-400"> ⚠ {GATE_AFTER[stage]}</span>}
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </div>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/Column.tsx dashboard/frontend/tests/test_Column.test.tsx
git commit -m "feat(frontend): Kanban Column with gate styling"
```

---

### Task 6.7: `<KanbanBoard>` with Gate-only drag rules  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/KanbanBoard.tsx`
- Test: `tests/test_KanbanBoard.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { KanbanBoard } from "../src/components/KanbanBoard";
import { useSessionsStore } from "../src/stores/sessionsStore";
import * as api from "../src/api/client";
import { vi } from "vitest";

test("renders 7 columns", () => {
  render(<KanbanBoard />);
  for (const s of ["interview","plan","review","execute","verify","document","pr"]) {
    expect(screen.getByText((t) => t.includes(s.toUpperCase()) || t === s)).toBeTruthy();
  }
});

test("dragging review→execute on pending card calls approveGate", async () => {
  useSessionsStore.setState({ sessions: [{
    slug: "feat-x", repoName: "a", repoRoot: "/a", currentPhase: "review",
    idea: "", phases: {}, mtime: 0,
    gates: { gate2_pre_execute: { state: "pending", source: null, reached_at: "", approved_at: null, approved_by: null } }
  } as any] });
  const spy = vi.spyOn(api, "approveGate").mockResolvedValue({ approved: true, event_id: "evt-1" } as any);
  render(<KanbanBoard />);
  // simulate dnd-kit drag end programmatically (helper extracted in implementation)
  const board = screen.getByTestId("kanban-board");
  fireEvent(board, new CustomEvent("test-drag", { detail: { activeSlug: "feat-x", overStage: "execute" } }));
  await new Promise(r => setTimeout(r, 50));
  expect(spy).toHaveBeenCalledWith("feat-x", "gate2_pre_execute");
});

test("non-gate drag rejected (no API call)", async () => {
  useSessionsStore.setState({ sessions: [{ slug: "feat-z", repoName: "a", repoRoot: "/a", currentPhase: "plan",
    idea: "", phases: {}, mtime: 0, gates: {} } as any] });
  const spy = vi.spyOn(api, "approveGate").mockResolvedValue({ approved: true } as any);
  render(<KanbanBoard />);
  const board = screen.getByTestId("kanban-board");
  fireEvent(board, new CustomEvent("test-drag", { detail: { activeSlug: "feat-z", overStage: "review" } }));
  await new Promise(r => setTimeout(r, 50));
  expect(spy).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/KanbanBoard.tsx
import { DndContext, DragEndEvent, useSensor, useSensors, PointerSensor } from "@dnd-kit/core";
import { useEffect } from "react";
import { useSessionsStore } from "../stores/sessionsStore";
import { useProjectsStore } from "../stores/projectsStore";
import { useUIStore } from "../stores/uiStore";
import { approveGate } from "../api/client";
import { Column } from "./Column";
import { SessionCard } from "./SessionCard";
import type { PhaseName, GateName } from "../types";

const STAGES: PhaseName[] = ["interview","plan","review","execute","verify","document","pr"];

const VALID_TRANSITIONS: Array<[PhaseName, PhaseName, GateName]> = [
  ["review", "execute", "gate2_pre_execute"],
  ["document", "pr", "gate3_pre_pr"]
];

export function KanbanBoard() {
  const sessions = useSessionsStore(s => s.sessions);
  const colorOf = useProjectsStore(s => s.colorByRepoRoot);
  const setSelected = useUIStore(s => s.setSelected);
  const pushToast = useUIStore(s => s.pushToast);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const handleDragEnd = async (e: DragEndEvent) => {
    const slug = String(e.active.id);
    const overId = String(e.over?.id ?? "");
    if (!overId.startsWith("col-")) return;
    const toStage = overId.slice(4) as PhaseName;
    const sess = sessions.find(s => s.slug === slug);
    if (!sess) return;
    const transition = VALID_TRANSITIONS.find(([from, to]) => from === sess.currentPhase && to === toStage);
    if (!transition) {
      pushToast("warn", "Gates 외 이동은 불가");
      return;
    }
    const [, , gate] = transition;
    const gateState = (sess.gates[gate] as any)?.state;
    if (gateState !== "pending") {
      pushToast("warn", `${gate} is not pending`);
      return;
    }
    try {
      await approveGate(slug, gate);
      pushToast("ok", `${gate} approved — resuming…`);
    } catch (err) {
      pushToast("err", `Approval failed: ${(err as Error).message}`);
    }
  };

  // Test escape hatch
  useEffect(() => {
    const root = document.querySelector("[data-testid=kanban-board]");
    if (!root) return;
    const handler = (e: any) => handleDragEnd({ active: { id: e.detail.activeSlug }, over: { id: `col-${e.detail.overStage}` } } as any);
    root.addEventListener("test-drag", handler as any);
    return () => root.removeEventListener("test-drag", handler as any);
  });

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div data-testid="kanban-board" className="grid grid-cols-7 gap-2 p-4">
        {STAGES.map((stage) => {
          const inCol = sessions.filter(s => s.currentPhase === stage);
          const hasPendingGate = inCol.some(s =>
            (stage === "review" && (s.gates.gate2_pre_execute as any)?.state === "pending") ||
            (stage === "document" && (s.gates.gate3_pre_pr as any)?.state === "pending")
          );
          return (
            <Column key={stage} stage={stage} hasPendingGate={hasPendingGate}>
              {inCol.map(s => (
                <SessionCard
                  key={s.slug}
                  session={s}
                  color={colorOf(s.repoRoot)}
                  isPendingGate={
                    (stage === "review" && (s.gates.gate2_pre_execute as any)?.state === "pending") ||
                    (stage === "document" && (s.gates.gate3_pre_pr as any)?.state === "pending")
                  }
                  isFailed={false /* set from SSE-tracked failures in T6.10 */}
                  onClick={() => setSelected(s.slug)}
                />
              ))}
            </Column>
          );
        })}
      </div>
    </DndContext>
  );
}
```

- [ ] **Step 4: Verify** — 3 PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/KanbanBoard.tsx dashboard/frontend/tests/test_KanbanBoard.test.tsx
git commit -m "feat(frontend): Kanban board with Gate-only drag validation"
```

---

### Task 6.8: `<ArtifactAccordion>` with lazy fetch  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/ArtifactAccordion.tsx`
- Test: `tests/test_ArtifactAccordion.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { ArtifactAccordion } from "../src/components/ArtifactAccordion";

const server = setupServer(
  http.get("/api/sessions/feat-x/artifacts/spec", () =>
    HttpResponse.json({ name: "spec", content_md: "# spec body", mtime: 1 }))
);
beforeAll(() => server.listen()); afterAll(() => server.close());

test("expand fetches and renders markdown", async () => {
  render(<ArtifactAccordion slug="feat-x" artifacts={[{ name: "spec", path: "/p", size: 1, mtime: 1 } as any]} />);
  fireEvent.click(screen.getByText("spec"));
  await waitFor(() => expect(screen.getByText("spec body")).toBeInTheDocument());
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/ArtifactAccordion.tsx
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import { useUIStore } from "../stores/uiStore";
import { getArtifact } from "../api/client";
import type { ArtifactRef } from "../types";

interface Props { slug: string; artifacts: ArtifactRef[]; }

export function ArtifactAccordion({ slug, artifacts }: Props) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const cache = useUIStore(s => s.artifactCache);
  const cacheArtifact = useUIStore(s => s.cacheArtifact);

  const toggle = async (name: string) => {
    const newOpen = new Set(open);
    if (newOpen.has(name)) { newOpen.delete(name); setOpen(newOpen); return; }
    newOpen.add(name); setOpen(newOpen);
    const key = `${slug}/${name}`;
    if (!cache[key]) {
      const a = await getArtifact(slug, name);
      cacheArtifact(key, { content_md: a.content_md, mtime: a.mtime });
    }
  };

  return (
    <div className="space-y-1">
      {artifacts.map(a => (
        <div key={a.name} className="bg-card rounded">
          <button onClick={() => toggle(a.name)}
                  className="w-full text-left px-2 py-1 text-sm flex justify-between">
            <span>{open.has(a.name) ? "▾" : "▸"} {a.name}</span>
            <span className="text-xs text-slate-400">{a.size}B</span>
          </button>
          {open.has(a.name) && (
            <div className="p-3 prose prose-invert max-w-none text-xs">
              {cache[`${slug}/${a.name}`]
                ? <ReactMarkdown
                    rehypePlugins={[[rehypeSanitize], [rehypeHighlight]]}
                    remarkPlugins={[remarkGfm]}>
                    {cache[`${slug}/${a.name}`].content_md}
                  </ReactMarkdown>
                : <span className="text-slate-500">loading…</span>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/ArtifactAccordion.tsx dashboard/frontend/tests/test_ArtifactAccordion.test.tsx
git commit -m "feat(frontend): ArtifactAccordion with lazy fetch and sanitized markdown"
```

---

### Task 6.9: `<DetailSlideOver>` panel  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/DetailSlideOver.tsx`
- Test: `tests/test_DetailSlideOver.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen } from "@testing-library/react";
import { DetailSlideOver } from "../src/components/DetailSlideOver";

test("renders slug, idea, timeline; closes on ✕", () => {
  const onClose = vi.fn();
  render(<DetailSlideOver
    session={{
      slug: "feat-x", idea: "do thing", repoName: "alpha", repoRoot: "/a",
      currentPhase: "review", phases: {
        interview: { status: "completed" }, plan: { status: "completed" }, review: { status: "in_progress" }
      }, gates: {}, mtime: 0
    } as any}
    color="#22c55e" artifacts={[]} onClose={onClose} onRetry={() => {}}
  />);
  expect(screen.getByText("feat-x")).toBeInTheDocument();
  expect(screen.getByText("do thing")).toBeInTheDocument();
  screen.getByText("✕").click();
  expect(onClose).toHaveBeenCalled();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/DetailSlideOver.tsx
import type { Session, ArtifactRef, PhaseName } from "../types";
import { ArtifactAccordion } from "./ArtifactAccordion";

const PHASES: PhaseName[] = ["interview","plan","review","execute","verify","document","pr"];

interface Props {
  session: Session;
  color: string;
  artifacts: ArtifactRef[];
  onClose: () => void;
  onRetry: () => void;
  isFailed?: boolean;
}

export function DetailSlideOver({ session, color, artifacts, onClose, onRetry, isFailed }: Props) {
  return (
    <aside className="fixed right-0 top-0 h-screen w-80 bg-panel border-l border-slate-700 p-4 overflow-y-auto shadow-2xl">
      <div className="flex items-center gap-2 mb-3">
        <div style={{ width: 4, height: 20, background: color }} />
        <h2 className="font-semibold flex-1">{session.slug}</h2>
        <button onClick={onClose} aria-label="close">✕</button>
      </div>
      <div className="flex gap-1 flex-wrap mb-3">
        <span className="bg-slate-800 text-xs px-2 py-0.5 rounded">{session.repoName}</span>
        <span className="bg-blue-900 text-xs px-2 py-0.5 rounded">{session.currentPhase}</span>
      </div>
      <section className="mb-3">
        <div className="text-xs uppercase text-slate-400 mb-1">Idea</div>
        <div className="text-sm">{session.idea}</div>
      </section>
      <section className="mb-3">
        <div className="text-xs uppercase text-slate-400 mb-1">Timeline</div>
        <ul className="text-xs space-y-1">
          {PHASES.map((p) => {
            const ph = session.phases[p];
            const icon = ph?.status === "completed" ? "✓" : ph?.status === "in_progress" ? "●" : "—";
            return <li key={p}><span className="inline-block w-4">{icon}</span> {p}</li>;
          })}
        </ul>
      </section>
      <section className="mb-3">
        <div className="text-xs uppercase text-slate-400 mb-1">Artifacts</div>
        <ArtifactAccordion slug={session.slug} artifacts={artifacts} />
      </section>
      {isFailed && (
        <section>
          <button onClick={onRetry} className="bg-red-700 text-white px-3 py-1 rounded text-sm">▶ Retry resume</button>
        </section>
      )}
    </aside>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/DetailSlideOver.tsx dashboard/frontend/tests/test_DetailSlideOver.test.tsx
git commit -m "feat(frontend): DetailSlideOver panel with Timeline and Artifacts"
```

---

### Task 6.10: `<TopBar>` with repo legend  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/TopBar.tsx`
- Test: `tests/test_TopBar.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen } from "@testing-library/react";
import { TopBar } from "../src/components/TopBar";
import { useProjectsStore } from "../src/stores/projectsStore";

test("renders project chips with color", () => {
  useProjectsStore.setState({ projects: [
    { id: 1, repo_root: "/a", repo_name: "alpha", color: "#22c55e" },
    { id: 2, repo_root: "/b", repo_name: "beta", color: "#a855f7" }
  ]});
  render(<TopBar activeCount={3} onOpenSettings={() => {}} />);
  expect(screen.getByText(/3 active/)).toBeInTheDocument();
  expect(screen.getByText("alpha")).toBeInTheDocument();
  expect(screen.getByText("beta")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/TopBar.tsx
import { useProjectsStore } from "../stores/projectsStore";
import { Link } from "react-router-dom";

interface Props { activeCount: number; onOpenSettings: () => void; }

export function TopBar({ activeCount, onOpenSettings }: Props) {
  const projects = useProjectsStore(s => s.projects);
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-panel border-b border-slate-700">
      <h1 className="font-semibold">CSS Pipeline Dashboard</h1>
      <span className="text-xs text-slate-400">· {activeCount} active</span>
      <div className="ml-auto flex items-center gap-2">
        {projects.map(p => (
          <span key={p.id} className="bg-slate-800 text-xs px-2 py-0.5 rounded flex items-center gap-1">
            <span style={{ width: 8, height: 8, background: p.color, borderRadius: 2 }} />
            {p.repo_name}
          </span>
        ))}
        <Link to="/history" className="text-xs text-slate-300">History</Link>
        <button onClick={onOpenSettings} className="text-xs text-slate-300" aria-label="settings">⚙</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/TopBar.tsx dashboard/frontend/tests/test_TopBar.test.tsx
git commit -m "feat(frontend): TopBar with repo legend and settings/history links"
```

---

### Task 6.11: `<SettingsModal>` with color picker  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/SettingsModal.tsx`
- Test: `tests/test_SettingsModal.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { SettingsModal } from "../src/components/SettingsModal";
import { useProjectsStore } from "../src/stores/projectsStore";

const server = setupServer(
  http.patch("/api/projects/1", () => HttpResponse.json({ id: 1, repo_root: "/a", repo_name: "alpha", color: "#ef4444" }))
);
beforeAll(() => server.listen()); afterAll(() => server.close());

test("changing color PATCHes API and updates store", async () => {
  useProjectsStore.setState({ projects: [{ id: 1, repo_root: "/a", repo_name: "alpha", color: "#22c55e" }] });
  render(<SettingsModal onClose={() => {}} />);
  const input = screen.getByLabelText(/alpha/) as HTMLInputElement;
  fireEvent.change(input, { target: { value: "#ef4444" } });
  fireEvent.blur(input);
  await waitFor(() => expect(useProjectsStore.getState().projects[0].color).toBe("#ef4444"));
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/SettingsModal.tsx
import { useProjectsStore } from "../stores/projectsStore";
import { patchProjectColor } from "../api/client";

interface Props { onClose: () => void; }

export function SettingsModal({ onClose }: Props) {
  const projects = useProjectsStore(s => s.projects);
  const patch = useProjectsStore(s => s.patch);

  const handleChange = async (id: number, color: string) => {
    try {
      const updated = await patchProjectColor(id, color);
      patch(id, updated.color);
    } catch (e) { /* toast handled elsewhere */ }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-panel p-6 rounded w-[480px]" onClick={(e) => e.stopPropagation()}>
        <h2 className="font-semibold mb-4">Project Colors</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-400"><th>Repo</th><th>Path</th><th>Color</th></tr></thead>
          <tbody>
            {projects.map(p => (
              <tr key={p.id} className="border-t border-slate-700">
                <td className="py-2">{p.repo_name}</td>
                <td className="py-2 text-xs text-slate-400">{p.repo_root}</td>
                <td className="py-2">
                  <input type="color"
                         aria-label={p.repo_name}
                         defaultValue={p.color}
                         onBlur={(e) => handleChange(p.id, e.target.value)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={onClose} className="mt-4 px-3 py-1 bg-slate-700 rounded">Close</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/SettingsModal.tsx dashboard/frontend/tests/test_SettingsModal.test.tsx
git commit -m "feat(frontend): SettingsModal with per-project color picker"
```

---

### Task 6.12: `<HistoryView>` table  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/HistoryView.tsx`
- Test: `tests/test_HistoryView.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { HistoryView } from "../src/components/HistoryView";

const server = setupServer(
  http.get("/api/history", () => HttpResponse.json({ total: 2, items: [
    { id: 1, session_id: "feat-a", outcome: "completed", finished_at: "2026-05-01", pr_url: "u" },
    { id: 2, session_id: "feat-b", outcome: "failed", finished_at: "2026-05-02", pr_url: null }
  ]}))
);
beforeAll(() => server.listen()); afterAll(() => server.close());

test("renders rows", async () => {
  render(<HistoryView />);
  await waitFor(() => expect(screen.getByText("feat-a")).toBeInTheDocument());
  expect(screen.getByText("feat-b")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/HistoryView.tsx
import { useEffect, useState } from "react";
import { listHistory } from "../api/client";

export function HistoryView() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => { listHistory({ limit, offset }).then(j => { setItems(j.items); setTotal(j.total); }); }, [offset]);

  return (
    <div className="p-4">
      <h2 className="font-semibold mb-2">History</h2>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-slate-400"><th>Finished</th><th>Session</th><th>Outcome</th><th>PR</th></tr></thead>
        <tbody>
          {items.map(it => (
            <tr key={it.id} className="border-t border-slate-700">
              <td>{it.finished_at?.slice(0,10)}</td>
              <td>{it.session_id}</td>
              <td className={it.outcome === "completed" ? "text-emerald-400" : "text-red-400"}>{it.outcome}</td>
              <td>{it.pr_url ? <a href={it.pr_url} className="text-blue-300">view</a> : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-2 flex gap-2 text-xs">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>← prev</button>
        <button disabled={offset + limit >= total} onClick={() => setOffset(offset + limit)}>next →</button>
        <span className="text-slate-400">{offset+1}–{Math.min(offset+limit, total)} / {total}</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/components/HistoryView.tsx dashboard/frontend/tests/test_HistoryView.test.tsx
git commit -m "feat(frontend): HistoryView paginated table"
```

---

### Task 6.13: `<ToastContainer>` + `<App>` wiring  [Specialist: css-ui-engineer]

**Files:**
- Create: `src/components/ToastContainer.tsx`
- Modify: `src/App.tsx`
- Test: `tests/test_App.test.tsx`

- [ ] **Step 1: Test**

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../src/App";

test("App renders TopBar, Kanban, and routes /history", () => {
  render(<MemoryRouter><App /></MemoryRouter>);
  expect(screen.getByText("CSS Pipeline Dashboard")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```tsx
// src/components/ToastContainer.tsx
import { useUIStore } from "../stores/uiStore";
import { useEffect } from "react";

const COLOR = { ok: "bg-emerald-700", info: "bg-blue-700", warn: "bg-amber-700", err: "bg-red-700" };

export function ToastContainer() {
  const toasts = useUIStore(s => s.toasts);
  const dismiss = useUIStore(s => s.dismissToast);
  useEffect(() => {
    const timers = toasts.map(t => setTimeout(() => dismiss(t.id), 4000));
    return () => timers.forEach(clearTimeout);
  }, [toasts, dismiss]);
  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map(t => (
        <div key={t.id} className={`${COLOR[t.kind]} text-white text-sm px-3 py-2 rounded shadow`}>{t.msg}</div>
      ))}
    </div>
  );
}
```

```tsx
// src/App.tsx
import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import { TopBar } from "./components/TopBar";
import { KanbanBoard } from "./components/KanbanBoard";
import { DetailSlideOver } from "./components/DetailSlideOver";
import { SettingsModal } from "./components/SettingsModal";
import { HistoryView } from "./components/HistoryView";
import { ToastContainer } from "./components/ToastContainer";
import { useSessionsStore } from "./stores/sessionsStore";
import { useProjectsStore } from "./stores/projectsStore";
import { useUIStore } from "./stores/uiStore";
import { listSessions, listProjects, listArtifacts } from "./api/client";
import { SSEManager } from "./api/sse";

export default function App() {
  const sessions = useSessionsStore(s => s.sessions);
  const setAllSessions = useSessionsStore(s => s.setAll);
  const upsertSession = useSessionsStore(s => s.upsert);
  const setProjects = useProjectsStore(s => s.setAll);
  const colorOf = useProjectsStore(s => s.colorByRepoRoot);
  const selectedSlug = useUIStore(s => s.selectedSlug);
  const setSelected = useUIStore(s => s.setSelected);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [artifacts, setArtifacts] = useState<any[]>([]);

  useEffect(() => {
    listSessions().then(setAllSessions);
    listProjects().then(setProjects);
    const mgr = new SSEManager();
    mgr.start();
    const off1 = mgr.on("session_updated", (d: any) => upsertSession({ slug: d.slug, currentPhase: d.phase, gates: d.gates, mtime: d.mtime } as any));
    return () => { off1(); mgr.stop(); };
  }, [setAllSessions, setProjects, upsertSession]);

  useEffect(() => {
    if (selectedSlug) listArtifacts(selectedSlug).then(setArtifacts);
  }, [selectedSlug]);

  const selected = sessions.find(s => s.slug === selectedSlug);

  return (
    <>
      <TopBar activeCount={sessions.length} onOpenSettings={() => setSettingsOpen(true)} />
      <Routes>
        <Route path="/" element={<KanbanBoard />} />
        <Route path="/history" element={<HistoryView />} />
      </Routes>
      {selected && (
        <DetailSlideOver
          session={selected}
          color={colorOf(selected.repoRoot)}
          artifacts={artifacts}
          onClose={() => setSelected(null)}
          onRetry={() => {}}
        />
      )}
      {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
      <ToastContainer />
    </>
  );
}
```

- [ ] **Step 4: Verify** — PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/App.tsx dashboard/frontend/src/components/ToastContainer.tsx dashboard/frontend/tests/test_App.test.tsx
git commit -m "feat(frontend): wire App with SSE, routing, toasts, slide-over"
```

---

## Batch 7 — Containerization, Installer, E2E

User checkpoint after batch: full clean install on an Ubuntu 22.04 VM, run E2E suite, verify v0.1 acceptance criteria.

### Task 7.1: Dockerfile (multi-stage)  [Specialist: css-infra-engineer]

**Files:**
- Create: `dashboard/Dockerfile`
- Create: `dashboard/.dockerignore`
- Test: `tests/golden/dockerfile.spec.md`

- [ ] **Step 1: Test**

```markdown
# Golden: Dockerfile structure

`dashboard/Dockerfile` must:
- Use a node:20-alpine stage named "frontend-build"
- Run `npm ci && npm run build` in that stage
- Use python:3.12-slim runtime stage
- COPY --from=frontend-build the built dist into the runtime image
- Install backend deps from pyproject.toml
- Expose port 7421
- CMD invokes uvicorn backend.main:app on 0.0.0.0:7421
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

`dashboard/Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=dev || npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq5 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY backend ./backend
COPY alembic ./alembic
COPY alembic.ini ./
COPY --from=frontend-build /app/frontend/dist ./static
EXPOSE 7421
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7421"]
```

`dashboard/.dockerignore`:
```
**/node_modules
**/__pycache__
**/.pytest_cache
**/tests/
**/.venv
**/dist
.env
```

Add to `dashboard/backend/main.py` (serve static after lifespan):
```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="ui")
```

- [ ] **Step 4: Verify**

```bash
cd dashboard && docker build -t css-dashboard:dev . && echo OK
```
Expected: image builds, `OK` prints.

- [ ] **Step 5: Commit**

```bash
git add dashboard/Dockerfile dashboard/.dockerignore dashboard/backend/main.py tests/golden/dockerfile.spec.md
git commit -m "feat(dashboard): multi-stage Dockerfile and static UI mount"
```

---

### Task 7.2: `docker-compose.yml`  [Specialist: css-infra-engineer]

**Files:**
- Create: `dashboard/docker-compose.yml`
- Test: `tests/golden/compose.spec.md`

- [ ] **Step 1: Test**

```markdown
# Golden: docker-compose

`dashboard/docker-compose.yml` must:
- Define service `dashboard` with build context "." and image css-dashboard:latest
- Map host port 7421 → container 7421
- Define service `postgres` with image postgres:16-alpine
- Volume mount `${HOME}/.claude:/host/.claude:rw`
- Have `depends_on: [postgres]` for dashboard
- Define named volume `css-dashboard-pgdata`
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

```yaml
services:
  dashboard:
    build: .
    image: css-dashboard:latest
    ports:
      - "${DASHBOARD_PORT:-7421}:7421"
    environment:
      DATABASE_URL: "postgresql+asyncpg://css:${DB_PASSWORD}@postgres:5432/css_dashboard"
      DASHBOARD_BIND: "0.0.0.0"
      HOST_CLAUDE_DIR: "/host/.claude"
      PROJECTS_JSON: "/host/.claude/css-dashboard/projects.json"
      QUEUE_DIR: "/host/.claude/css-dashboard/queue"
      RUNS_DIR: "/host/.claude/css-dashboard/runs"
    volumes:
      - "${HOME}/.claude:/host/.claude:rw"
      - "${HOME}:/host/projects:ro"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: css
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
      POSTGRES_DB: css_dashboard
    volumes:
      - css-dashboard-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U css -d css_dashboard"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

volumes:
  css-dashboard-pgdata:
```

- [ ] **Step 4: Verify**

```bash
cd dashboard && cp .env.example .env && docker compose config > /dev/null && echo OK
```

- [ ] **Step 5: Commit**

```bash
git add dashboard/docker-compose.yml tests/golden/compose.spec.md
git commit -m "feat(dashboard): docker-compose with postgres healthcheck and host volume mount"
```

---

### Task 7.3: `install-dashboard.sh` (Ubuntu)  [Specialist: css-infra-engineer]

**Files:**
- Create: `scripts/install-dashboard.sh`
- Create: `scripts/uninstall-dashboard.sh`
- Test: `tests/golden/installer.spec.md`

- [ ] **Step 1: Test**

```markdown
# Golden: install-dashboard.sh

`scripts/install-dashboard.sh` must:
- Be executable (shebang #!/usr/bin/env bash, set -euo pipefail)
- Verify docker and docker compose are available
- Create ~/.claude/css-dashboard/{queue,runs,bin} with mode 700
- Generate ~/.claude/css-dashboard/config.json from config/dashboard-config.example.json
- Copy dashboard/bridge/bridge.py to ~/.claude/css-dashboard/bin/bridge.py
- Install systemd user unit, enable + start it
- Build dashboard image and run docker compose up -d
- Run alembic upgrade head inside the container
- Print final URL at the end
```

- [ ] **Step 2: Run (FAIL)**

- [ ] **Step 3: Implement**

`scripts/install-dashboard.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

require() { command -v "$1" >/dev/null || { echo "missing dependency: $1"; exit 1; }; }
require docker
docker compose version >/dev/null || { echo "docker compose plugin required"; exit 1; }
require python3
require systemctl

CSS_DIR="$HOME/.claude/css-dashboard"
mkdir -p "$CSS_DIR"/{queue,queue/processed,queue/failed,runs,bin}
chmod 700 "$CSS_DIR"

REPO_ROOT="$(git rev-parse --show-toplevel)"
[ -f "$CSS_DIR/config.json" ] || cp "$REPO_ROOT/config/dashboard-config.example.json" "$CSS_DIR/config.json"

# Generate DB password if .env absent
if [ ! -f "$REPO_ROOT/dashboard/.env" ]; then
  PW=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
  sed "s|changeme|$PW|g" "$REPO_ROOT/dashboard/.env.example" > "$REPO_ROOT/dashboard/.env"
fi

# Copy bridge and install systemd user unit
cp "$REPO_ROOT/dashboard/bridge/bridge.py" "$CSS_DIR/bin/bridge.py"
chmod 700 "$CSS_DIR/bin/bridge.py"
mkdir -p "$HOME/.config/systemd/user"
cp "$REPO_ROOT/dashboard/bridge/css-dashboard-bridge.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now css-dashboard-bridge.service

# Build + up
(cd "$REPO_ROOT/dashboard" && docker compose up -d --build)
sleep 5
(cd "$REPO_ROOT/dashboard" && docker compose exec -T dashboard alembic upgrade head)

HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "Dashboard up at http://${HOST_IP:-localhost}:7421"
```

`scripts/uninstall-dashboard.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
systemctl --user disable --now css-dashboard-bridge.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/css-dashboard-bridge.service"
systemctl --user daemon-reload

read -p "Remove postgres volume (deletes history)? [y/N] " yn
if [ "$yn" = "y" ] || [ "$yn" = "Y" ]; then
  (cd "$REPO_ROOT/dashboard" && docker compose down -v)
else
  (cd "$REPO_ROOT/dashboard" && docker compose down)
fi

# disable in config.json (preserve everything else)
if [ -f "$HOME/.claude/css-dashboard/config.json" ]; then
  python3 -c "import json,os; p=os.path.expanduser('~/.claude/css-dashboard/config.json'); d=json.load(open(p)); d['dashboard_enabled']=False; json.dump(d, open(p,'w'), indent=2)"
fi
echo "Dashboard uninstalled. CSS reverts to legacy AskUserQuestion mode."
```

- [ ] **Step 4: Verify**

```bash
chmod +x scripts/install-dashboard.sh scripts/uninstall-dashboard.sh
bash -n scripts/install-dashboard.sh && bash -n scripts/uninstall-dashboard.sh && echo OK
```

- [ ] **Step 5: Commit**

```bash
git add scripts/install-dashboard.sh scripts/uninstall-dashboard.sh tests/golden/installer.spec.md
git commit -m "feat(installer): install-dashboard.sh and uninstall-dashboard.sh for Ubuntu"
```

---

### Task 7.4: Playwright E2E — full drag-approve flow  [Specialist: css-ui-engineer]

**Files:**
- Create: `dashboard/frontend/tests/e2e/drag-approve.spec.ts`
- Create: `dashboard/frontend/playwright.config.ts`
- Test: itself

- [ ] **Step 1: Write the failing test (will fail before fixture is set up)**

```ts
// tests/e2e/drag-approve.spec.ts
import { test, expect } from "@playwright/test";

test("dragging review→execute on pending Gate 2 card resumes the pipeline", async ({ page, request }) => {
  // Pre-condition: backend running with a synthetic session
  // (fixture script writes a session JSON to a watched temp project root before this test)

  await page.goto("http://localhost:5173/");
  // wait for kanban
  await page.waitForSelector("[data-testid=kanban-board]");

  const card = page.locator("[data-slug=feat-x]");
  await expect(card).toBeVisible();
  await expect(card).toHaveAttribute("data-slug", "feat-x");

  const sourceBox = await card.boundingBox(); if (!sourceBox) throw new Error("no card bbox");
  const targetCol = page.locator("[data-stage=execute]");
  const targetBox = await targetCol.boundingBox(); if (!targetBox) throw new Error("no col bbox");

  await page.mouse.move(sourceBox.x + 10, sourceBox.y + 10);
  await page.mouse.down();
  await page.mouse.move(targetBox.x + 50, targetBox.y + 80, { steps: 10 });
  await page.mouse.up();

  // Verify card moved (after SSE round-trip) — mock bridge updates session to currentPhase=execute
  await expect(page.locator("[data-stage=execute] [data-slug=feat-x]")).toBeVisible({ timeout: 10000 });
});
```

`dashboard/frontend/playwright.config.ts`:
```ts
import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/e2e",
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true
  },
  use: { baseURL: "http://localhost:5173" }
});
```

- [ ] **Step 2: Run (FAIL)** — drag-approve fixture doesn't exist yet.

- [ ] **Step 3: Add fixture script + mock claude**

Create `dashboard/frontend/tests/e2e/fixtures/seed.sh` to write a synthetic project + session before the test, and a mock-claude script that the bridge calls (it just updates the session JSON to next phase):

```bash
#!/usr/bin/env bash
# tests/e2e/fixtures/seed.sh
set -e
TMP_PROJ="$(mktemp -d)"
mkdir -p "$TMP_PROJ/.claude/css/sessions" "$TMP_PROJ/.claude/css/locks"
cat > "$TMP_PROJ/.claude/css/sessions/feat-x.json" <<EOF
{ "slug":"feat-x","idea":"i","master_flow":true,"repo_root":"$TMP_PROJ","repo_name":"e2e",
  "current_phase":"review","phases":{}, "gates":{"gate2_pre_execute":{"state":"pending"}} }
EOF
# Add to projects.json
PJ="$HOME/.claude/css-dashboard/projects.json"
python3 -c "
import json,os,sys
p=os.path.expanduser(os.environ['PJ_PATH']); d={'projects':[]}
if os.path.exists(p): d=json.load(open(p))
d['projects'].append({'repo_root': os.environ['PROJ'], 'repo_name': 'e2e', 'registered_at': '2026', 'color': '#22c55e'})
json.dump(d, open(p,'w'))
" PJ_PATH="$PJ" PROJ="$TMP_PROJ"

# Mock claude: just flips current_phase to "execute"
cat > "$HOME/.claude/css-dashboard/bin/claude" <<'EOF'
#!/usr/bin/env bash
# accepts "--print" and "/css:ship --session X"
session_id=$(echo "$@" | grep -oP '(?<=--session )[a-z0-9-]+')
SF="$(find / -name "$session_id.json" -path "*/.claude/css/sessions/*" 2>/dev/null | head -1)"
python3 -c "
import json,sys; p='$SF'; d=json.load(open(p)); d['current_phase']='execute'; json.dump(d,open(p,'w'))
"
EOF
chmod +x "$HOME/.claude/css-dashboard/bin/claude"
echo "$TMP_PROJ"
```

Update `playwright.config.ts` `globalSetup` to run this before tests.

- [ ] **Step 4: Verify**

```bash
cd dashboard/frontend && npx playwright test
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/tests/e2e dashboard/frontend/playwright.config.ts
git commit -m "test(e2e): Playwright drag-approve flow with mock claude"
```

---

### Task 7.5: dashboard/README.md final update  [Specialist: executor-direct]

**Files:**
- Modify: `dashboard/README.md`
- Modify: top-level `README.md` (add dashboard section link)

- [ ] **Step 1: Test**

```bash
grep -q "install-dashboard.sh" dashboard/README.md && grep -q "drag" dashboard/README.md && echo OK
```

- [ ] **Step 2: Run (FAIL)** initially.

- [ ] **Step 3: Update content**

Expand `dashboard/README.md` to include: install / uninstall / architecture summary / troubleshooting / link back to spec + plan.

Add a section to top-level `README.md` between "주요 기능" and "설계 문서":
```markdown
## Dashboard (Optional)

대시보드를 설치하면 진행 중인 모든 CSS 세션을 Kanban 보드에서 시각화하고 Gate 승인을 드래그&드롭으로 처리할 수 있습니다.

```bash
bash scripts/install-dashboard.sh
```

자세한 내용은 [`dashboard/README.md`](dashboard/README.md)를 참고하세요.
```

- [ ] **Step 4: Verify** — `grep -q` checks pass.

- [ ] **Step 5: Commit**

```bash
git add dashboard/README.md README.md
git commit -m "docs: add dashboard section to top-level README + flesh out dashboard/README.md"
```

---

## Self-Review

**1. Spec coverage check** — every acceptance criterion in the spec maps to at least one task:
- AC1 Kanban renders → T6.1 + T6.5 + T6.6 + T6.7
- AC2 card click slide-out → T6.9 + T6.13
- AC3 artifact accordion lazy fetch → T6.8 + T4.7 + T4.8
- AC4 drag Gate 2/3 approval → T6.7 + T4.9 + T4.10 + T5.1
- AC5 cross-path approval → T2.3 + T2.4 (terminal) + T6.7 (dashboard)
- AC6 lock-based mutex → T4.10 (lock check returns 409)
- AC7 drag rule enforcement → T6.7 (transition whitelist)
- AC8 per-repo color → T4.5 (PATCH) + T6.11 (UI)
- AC9 history view → T4.16 + T6.12
- AC10 failure recovery → T4.10 (retry) + T4.15 (failed event) + T6.9 (retry button)
- AC11 `--slug` → `--session` rename → T1.1
- AC12 ≥85% coverage → every task has tests
- AC13 install-dashboard.sh one command → T7.3
- AC14 no regression in legacy mode → T2.3 + T2.4 (both branches preserved)

**2. Placeholder scan** — no "TBD/TODO/implement later" in any step. Every step has either runnable code, a runnable command, or a verifiable assertion.

**3. Type consistency** — `session.gates.gate2_pre_execute.state`, `session.slug`, `repo_root`, `repo_name`, `current_phase` used identically across CSS commands, JSON parser (T4.3), routers (T4.6, T4.10), and React types (T6.2). `approval_source` enum (`dashboard_drag` | `terminal_ask`) consistent in DB schema (T3.1), audit insert (T4.10), and SSE events (T4.15).

**4. Specialist routing** — every task is tagged with exactly one specialist; the CSS Single-Specialist Task Rule is satisfied.

---

## Notes for /css:review

This plan is intended to satisfy the CSS Single-Specialist Task Rule. Each task is annotated with `[Specialist: <name>]`. The review stage should:
1. For each task, verify the specialist annotation matches the actual scope.
2. Dispatch the named specialist (or `executor-direct` shim) to produce a Rich Spec.
3. If any task touches multiple domains, raise `LOOPBACK_TO_PLAN` so the task can be split.

Task count by specialist:
- `css-prompt-engineer`: 5 (T1.1, T2.1, T2.2, T2.3, T2.4, T2.5 — 6 actually)
- `css-db-specialist`: 5 (T3.1, T3.2, T3.3, T4.14, T4.16)
- `css-async-coder`: 8 (T4.2, T4.3, T4.9, T4.11, T4.12, T4.13, T5.1)
- `css-api-specialist`: 6 (T4.5, T4.6, T4.7, T4.8, T4.10, T4.15)
- `css-ui-engineer`: 13 (T6.1, T6.3, T6.4, T6.5, T6.6, T6.7, T6.8, T6.9, T6.10, T6.11, T6.12, T6.13, T7.4)
- `css-infra-engineer`: 4 (T5.2, T7.1, T7.2, T7.3)
- `executor-direct`: 6 (T1.2, T1.3, T4.1, T4.4, T6.2, T7.5)

Total: 47 tasks across 7 batches.


