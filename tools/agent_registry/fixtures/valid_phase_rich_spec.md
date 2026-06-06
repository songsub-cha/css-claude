## Task 02
Specialist: css-api-specialist
Phase: 2
Files:
- app/api.py
Verification mode: command
RED scaffold:
```python
def test_new_endpoint(): assert False
```
RED command: uv run pytest tests/test_api.py
GREEN template:
```python
def endpoint(): return "ok"
```
GREEN command: uv run pytest tests/test_api.py
Edge cases: invalid input
Depends-on: none
Cross_Domain_Notes: none
ARTIFACT=.claude/css/plans/epic-p2-T02.md
