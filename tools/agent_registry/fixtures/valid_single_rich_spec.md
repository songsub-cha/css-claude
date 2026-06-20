## Task 01
Specialist: css-ui-engineer
Phase: 1
Files:
- src/App.tsx
Verification mode: command
RED scaffold:
```tsx
it("renders", () => expect(false).toBe(true))
```
RED command: npm test -- App.test.tsx
GREEN template:
```tsx
export function App() { return <main /> }
```
GREEN command: npm test -- App.test.tsx
Edge cases: empty state
Depends-on: none
Cross_Domain_Notes: none
ARTIFACT=.claude/css/plans/small-idea-T01.md
