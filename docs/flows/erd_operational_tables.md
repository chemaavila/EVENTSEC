ERD (operational tables)
erDiagram
  USERS ||--o{ HANDOVERS : creates
  USERS ||--o{ WORKPLANS : owns
  WORKPLANS ||--o{ WORKPLAN_ITEMS : has
  WORKPLANS ||--|| WORKPLAN_FLOW : has
  ALERTS ||--o{ WAR_ROOM_NOTES : has
  USERS ||--o{ WAR_ROOM_NOTES : writes
  ATTACHMENTS ||--o{ WAR_ROOM_NOTES : attaches
  ALERTS ||--o{ NOTIFICATION_EVENTS : emits
