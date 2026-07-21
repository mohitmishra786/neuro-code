# NeuroCode UI & Design Tokens

Desktop-first hierarchical graph explorer (React + ReactFlow). Mobile/touch is **not** a supported primary target in 0.1.x.

## Layout

- Header: logo, search, controls, live WebSocket indicator, theme toggle  
- Breadcrumbs for hierarchy path  
- Main canvas: ReactFlow graph + floating legend  
- Sidebar: selected node details  

## Node colors (single source of truth)

TypeScript: `frontend/src/constants/nodeColors.ts`  
CSS variables: `frontend/src/App.css` (`--node-*`)

| Type | Hex | CSS var |
|------|-----|---------|
| Package | `#6366f1` | `--node-package` |
| Module | `#8b5cf6` | `--node-module` |
| Class | `#10b981` | `--node-class` |
| Function | `#f59e0b` | `--node-function` |
| Variable | `#ec4899` | `--node-variable` |
| Unknown | `#64748b` | — |

## Edge styles

See `EDGE_STYLES` in `nodeColors.ts` and Architecture docs:

| Edge | Visual |
|------|--------|
| CONTAINS | Solid gray |
| CALLS | Dashed amber |
| IMPORTS | Dotted indigo |
| INHERITS | Thick emerald |

## Tokens (CSS)

Defined under `:root` in `App.css`: background, surface, glass, borders, text levels, accent, spacing (`--space-*`), radii, transitions, shadows.

Default theme is **dark** (`#0a0a0f`). Light mode via `data-theme="light"`.

## Accessibility notes

- Body text targets ≥4.5:1 contrast on surfaces  
- Edge stroke opacity increased for visibility on dark canvas  
- Keyboard navigation for graph is incomplete in 0.1.x (tracked as EDGE issues)  
- Prefer desktop mouse/trackpad for expand (double-click)
