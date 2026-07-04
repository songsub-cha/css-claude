# Golden Test: wiki-project-docs

Asserts `/css:wiki` + `css-doc-curator` keep the docs/project/ living-docs contract.

## Acceptance criteria

### agents/doc-curator.md
- `grep -c "name: css-doc-curator" agents/doc-curator.md` >= 1
- `grep -c "css_stages: \[wiki\]" agents/doc-curator.md` >= 1
- `grep -c "ARTIFACT=docs/project/" agents/doc-curator.md` >= 1
- `grep -c "css:updated" agents/doc-curator.md` >= 1
- `grep -c "features/README.md" agents/doc-curator.md` >= 1
- `grep -c "미확인" agents/doc-curator.md` >= 1
- `grep -c "git commit" agents/doc-curator.md` >= 1  (커밋 금지 조항)

### commands/wiki.md
- `grep -c "css-doc-curator" commands/wiki.md` >= 1
- `grep -c "css:last-synced" commands/wiki.md` >= 1
- `grep -c "wiki-publish" commands/wiki.md` >= 1
- `grep -c "adr-list" commands/wiki.md` >= 1
- `grep -c "_project-wiki.lock" commands/wiki.md` >= 1
- `grep -c "AskUserQuestion" commands/wiki.md` >= 1
- `grep -c "docs/project/" commands/wiki.md` >= 3
