Workplan + ReactFlow persistence
flowchart TD
  A[User creates/edits Workplan] --> B{Validate}
  B -- ok --> C[POST/PATCH /api/workplans]
  C --> D[(Postgres: workplans)]
  D --> E[Return workplan_id]
  E --> F[Manage items]
  F --> G[POST/PATCH /api/workplans/:id/items]
  G --> H[(Postgres: workplan_items)]
  E --> I[Edit ReactFlow Diagram]
  I --> J[PUT /api/workplans/:id/flow]
  J --> K[(Postgres: workplan_flow)]
  K --> L[Reload: GET flow rehydrates nodes/edges/viewport]
  B -- error --> M[Inline errors]
