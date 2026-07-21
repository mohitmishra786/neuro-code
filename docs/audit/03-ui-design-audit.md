# Artifact 3: UI Design Audit

**Date of audit:** July 2026  
**Sources:** `frontend/src/` components/styles; no live demo or screenshots in repo

---

## Current State

### Critical gap (top finding)

**There are zero product screenshots, GIFs, videos, or linked live demos** in the README, docs, or repository assets (`find` for png/gif/jpg/webp under the project excluding node_modules returned none).  

For a **visualization tool**, this is a first-order product design failure for discoverability: GitHub visitors cannot see the product without completing a multi-service install (Artifact 4). Comparable 2026 tools (CodeLayers, Sourcegraph marketing, VS Code extension marketplaces) lead with interactive screenshots or embed GIFs.

### What is inferable from the frontend

| Surface | Implementation | Design notes |
|---------|----------------|--------------|
| Shell | `App.tsx` — header (logo, search, controls, theme), breadcrumbs, main graph + sidebar | Classic IDE-like three-zone layout |
| Graph | `TreeGraph.tsx` — ReactFlow, MiniMap, Controls, Background, custom `CircleNode` + `TypedEdge` | Hierarchical layout via dagre (TB) |
| Node vocabulary | Colors in `treeStore` / Architecture docs | Package indigo, module purple, class emerald, function amber, variable pink |
| Theme | `themeStore` + CSS variables in `App.css` | **Dark default** (`:root` navy-black `#0a0a0f`), light via `data-theme` |
| Visual language | Glassmorphism header, accent glow indigo `#6366f1`, Inter-like system stack | Aligns with 2024–26 “devtool dark” fashion |
| Empty state | “No Code Structure / Parse a Python codebase…” + tree emoji | Exists but no CTA linking to CLI/docs |
| Error state | Banner + graph error with Retry | Present |
| Node panel | `NodeInfoPanel` empty state when nothing selected | Present |
| Accessibility issues tracked | Open issues: keyboard nav (#152), tooltips (#151), label overlap (#150), touch (#145), minimap mobile (#147), contrast work partially done (commit “Improve MiniMap mask color contrast”) | Incomplete |

### Design tokens (actually in CSS)

`App.css` defines a solid token system:

- Backgrounds, surfaces, glass, borders, text levels  
- Accent + semantic success/warning/error  
- Node type CSS variables  
- Spacing scale (xs→2xl), radii, transitions, shadows  

This is **above average for a pre-launch OSS UI** — tokens exist; the gap is **proof and polish**, not absence of a system.

### 2026 conventions for graph/dev-tool UIs (from market research)

From CodeLayers 2026 guide imagery/descriptions, Sourcegraph product marketing, and common graph UIs:

| Convention | Market norm 2026 | NeuroCode |
|------------|------------------|-----------|
| Dark mode default | Near-universal for graph canvases | **Yes** |
| Color-by-type nodes | Common | **Yes** (typed palette) |
| Edge encoding | Color + stroke style | Documented (solid/dashed/dotted/thick) |
| Information density | Progressive disclosure over “hairball” | **Yes** (lazy expand) — strongest UI idea |
| Hero media | GIF/video of expand interaction | **Missing** |
| Spatial / 3D | Rising (CodeLayers Vision Pro/web) | Not claimed (and shouldn’t be) |
| Minimal chrome | Dense but clean | Header + sidebar approach is standard |

**Note:** README still markets “Sigma.js WebGL”; the actual UI is ReactFlow (DOM/SVG hybrid). Design narrative should match the real renderer (crisp hierarchical tree, not GPU particle graph).

---

## Gaps / Risks

1. **No visual marketing assets** — #1 growth/design blocker.
2. **Empty state is passive** — no “Run this command” or “Load demo dataset” button.
3. **Open EDGE issues** imply polish debt (overlap, mobile, keyboard).
4. **Contrast of gray edges on near-black canvas** (`--color-edge: rgba(148,163,184,0.3)`) may fail WCAG for edge visibility — needs measured check on real screenshots.
5. **Responsive behavior** undocumented; mobile issues explicitly open (#145, #147). Do not claim mobile-ready.
6. **Cannot fully audit visual quality** without running the app — this audit is structure-based only.

---

## Checklist

### Pre-Launch

- [ ] **Record a 15–30s hero GIF** (or silent MP4): load demo graph → double-click expand package → select class → search jump. (Effort: **M**). *Verify:* GIF in README top; file &lt;10MB or hosted.
- [ ] **3 still screenshots:** overview hierarchy, edge types visible, dark+light. (Effort: **S**)
- [ ] **README visual section** above the fold (before Requirements). (Effort: **S**)
- [ ] **Empty-state CTA** with exact command: `python scripts/parse_codebase.py ./examples/demo` (once demo exists). (Effort: **S**)
- [ ] **Legend component** for node/edge colors (in-app + README). (Effort: **S–M**)
- [ ] **Spot-check contrast** of nodes/edges/text with browser DevTools or axe. (Effort: **S**). *Verify:* body text ≥4.5:1; node labels readable.
- [ ] **Align marketing with ReactFlow** visuals (not WebGL claims). (Effort: **S**)
- [ ] **Close or defer mobile** — if not supporting touch, state “desktop recommended” in README. (Effort: **S**)

### Launch

- [ ] Social card / Open Graph image of the graph UI for HN/Twitter. (Effort: **S**)
- [ ] Use same GIF in Show HN first comment. (Effort: **S**)

### Post-Launch

- [ ] Address EDGE-P1 loading indicators (#141) if users report confusion. (Effort: **S**)
- [ ] Keyboard navigation path for power users (#152). (Effort: **M**)
- [ ] Consider density modes (compact vs comfortable) after feedback. (Effort: **L**)

### Design token consistency

- [ ] Audit that `NODE_COLORS` in TS and `--node-*` in CSS stay in sync (single source of truth preferred). (Effort: **S**)
- [ ] Document tokens in a short `docs/UI.md`. (Effort: **S**)
