# Issue labels

Apply consistently so setup friction is measurable (Artifact 11).

## Required funnel labels

| Label | Use when |
|-------|----------|
| `setup` | Install, Docker, Neo4j, first graph, empty UI after parse |
| `bug` | Incorrect behavior with reproduction steps |
| `enhancement` | New capability |
| `question` | Support / how-to |

## Priority / process (optional)

| Label | Use when |
|-------|----------|
| `launch-blocker` | Demo path broken |
| `good first issue` | Small, documented acceptance criteria |
| `agent-generated` | From automated analysis (not user-reported) |
| `priority:p0` / `p1` / `p2` | Historical agent priorities—prefer milestones instead |

## Create labels via `gh` (maintainer)

```bash
gh label create setup --color "B60205" --description "Install / first-graph friction" --force
gh label create bug --color "d73a4a" --description "Something isn't working" --force
gh label create enhancement --color "a2eeef" --description "New feature or request" --force
gh label create question --color "d876e3" --description "Further information is requested" --force
gh label create launch-blocker --color "b60205" --description "Breaks demo path" --force
gh label create agent-generated --color "ededed" --description "Auto static-analysis debt" --force
gh label create "good first issue" --color "7057ff" --description "Good for newcomers" --force
```
