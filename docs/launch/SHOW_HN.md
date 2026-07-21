# Show HN draft (DO NOT PUBLISH without maintainer confirmation)

**Suggested window:** Tuesday–Thursday, 8:00–10:00 America/New_York  
**Title:**

```
Show HN: NeuroCode – hierarchical knowledge graph for local Python codebases
```

**Body:**

```
I built NeuroCode for the “I just joined a huge Python monorepo” problem.

It parses a Python project with Tree-sitter, stores packages/classes/calls in Neo4j,
and lets you expand a hierarchical graph in the browser (ReactFlow)—fully local.

Why local: no uploading proprietary code to a SaaS map tool.
Why hierarchical: package → module → class → function matches how Python is organized
(vs. one giant force-directed hairball).

Stack: Tree-sitter, Neo4j, FastAPI, React + ReactFlow.
Limits: Python only today; early 0.1.x; Docker required; performance numbers are goals, not marketing claims.

Fastest path:

  git clone https://github.com/mohitmishra786/neuro-code
  cd neuro-code && make demo
  # open http://localhost:3000

Repo: https://github.com/mohitmishra786/neuro-code

Feedback welcome—especially setup pain and whether CALLS/INHERITS edges match your mental model.
```

**First comment:**

```
Maintainer here for the next ~2h.

GIF/diagram: see README hero.
Demo package is examples/demo_pkg (parsed by make demo).
Known limits: docs/launch/LIMITATIONS.md
Architecture: docs/ARCHITECTURE.md

If setup fails, open a GitHub issue with the setup label.
```
