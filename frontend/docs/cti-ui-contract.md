# CTI UI Contract (Wave 1)

## Phase 0 – repo map

### Routing + pages
- Router: `react-router-dom` configured in `frontend/src/App.tsx`.
- Existing pages live in `frontend/src/pages/` (examples: `DashboardPage.tsx`, `ThreatIntelPage.tsx`).
- New CTI Wave 1 routes are under `/intelligence/*` and map to `frontend/src/pages/Intelligence/`.

### Layout + navigation
- Global chrome (topbar + sidebar) is defined in `frontend/src/components/layout/Topbar.tsx` and `frontend/src/components/layout/Sidebar.tsx`.
- The new `/intelligence/*` routes suppress global chrome and render their own layout (per design frames).

### Theme + styling
- Global theme tokens and base styles live in `frontend/src/index.css` and `frontend/src/App.css`.
- CTI-specific styling is in `frontend/src/components/cti/cti.css` (scoped via class names; no Tailwind CDN usage).

### Auth / roles
- Auth is enforced via `ProtectedRoute` and `AdminRoute` in `frontend/src/App.tsx` using `frontend/src/contexts/AuthContext.tsx`.

### Data fetching + state
- Existing data utilities are in `frontend/src/services/api.ts`.
- CTI module uses `frontend/src/services/cti/*` with mock adapters by default.

### Tests
- No frontend test runner is configured in `frontend/package.json` at this time.

### How to run
```bash
cd frontend
npm run dev
```

### Env flags
- `VITE_CTI_USE_MOCK=true` (default): uses `frontend/src/services/cti/mockAdapter.ts`.
- `VITE_CTI_USE_MOCK=false`: uses `frontend/src/services/cti/apiAdapter.ts` (stub; not implemented yet).

## Wave 1 progress

### Routes (skeletons created)
- `/intelligence/dashboard` → `frontend/src/pages/Intelligence/IntelligenceDashboardPage.tsx` (implemented; Overview Dashboard)
- `/intelligence/search` → `frontend/src/pages/Intelligence/IntelligenceSearchPage.tsx` (implemented; Intelligence Search)
- `/intelligence/entity/:id` → `frontend/src/pages/Intelligence/IntelligenceEntityPage.tsx` (implemented; Entity Detail)
- `/intelligence/graph` → `frontend/src/pages/Intelligence/IntelligenceGraphPage.tsx` (implemented; Graph Explorer)
- `/intelligence/attack` → `frontend/src/pages/Intelligence/IntelligenceAttackPage.tsx` (implemented; ATT&CK Matrix)
- `/intelligence/indicators` → `frontend/src/pages/Intelligence/IntelligenceIndicatorsPage.tsx` (implemented; Indicators & Observables Hub)
- `/intelligence/reports` → `frontend/src/pages/Intelligence/IntelligenceReportsPage.tsx` (implemented; Reports)
- `/intelligence/cases` → `frontend/src/pages/Intelligence/IntelligenceCasesPage.tsx` (implemented; Cases)
- `/intelligence/playbooks` → `frontend/src/pages/Intelligence/IntelligencePlaybooksPage.tsx` (implemented; Playbooks)
- `/intelligence/connectors` → `frontend/src/pages/Intelligence/IntelligenceConnectorsPage.tsx` (implemented; Connectors)

### Fixtures
- `frontend/src/fixtures/cti/dashboard.ts` (Overview dashboard data)
- `frontend/src/fixtures/cti/search_results.ts` (Intelligence Search results)
- `frontend/src/fixtures/cti/entity_detail.ts` (Entity Detail data)
- `frontend/src/fixtures/cti/graph.ts` (Graph Explorer data)
- `frontend/src/fixtures/cti/attack_matrix.ts` (ATT&CK Matrix data)
- `frontend/src/fixtures/cti/indicators.ts` (Indicators & Observables data)
- `frontend/src/fixtures/cti/reports.ts` (Reports data)
- `frontend/src/fixtures/cti/cases.ts` (Cases data)
- `frontend/src/fixtures/cti/playbooks.ts` (Playbooks data)
- `frontend/src/fixtures/cti/connectors.ts` (Connectors data)

### Known gaps / assumptions
- CTI API adapter is stubbed; mock data is the default source.
- Remaining Wave 1 pages are placeholders until their design frames arrive.
