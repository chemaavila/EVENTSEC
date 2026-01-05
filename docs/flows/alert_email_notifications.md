Alert lifecycle → notification events → email
sequenceDiagram
  participant API as FastAPI (Alerts/Users)
  participant DB as Postgres
  participant NE as notification_events
  participant ES as EmailService (DEV outbox / PROD provider)
  participant M as Manager
  participant L1 as Level 1
  participant L2 as Level 2
  participant U as Assigned User
  API->>DB: Create/Update/Close/Escalate alert OR Create/Assign user
  API->>NE: Insert event (dedup key)
  alt not duplicate
    NE->>ES: Send(recipient list, template, payload)
    ES-->>M: Email (manager)
    alt level 1
      ES-->>L1: Email (L1 DL/users)
    else level 2
      ES-->>L2: Email (L2 DL/users)
    end
    ES-->>U: Email (assigned user when relevant)
    ES->>NE: Mark sent
  else duplicate
    NE->>NE: Mark skipped_dedup
  end
