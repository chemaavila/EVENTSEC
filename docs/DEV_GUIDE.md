# EventSec Developer Guide

## ORM conventions (SQLAlchemy)

These conventions prevent mapper ambiguity and keep relationships consistent.

### Relationship rules
- Every `relationship()` with `back_populates` must be mirrored on the related model.
- When a model has multiple foreign keys to the same table, **always** set `foreign_keys` on
  both sides of the relationship.
- Use explicit `back_populates` for ownership or assignment relationships to avoid implicit joins.

### Example pattern
```python
class Alert(Base):
    owner_id = mapped_column(ForeignKey("users.id"))
    assigned_to = mapped_column(ForeignKey("users.id"))

    owner = relationship("User", back_populates="alerts", foreign_keys=[owner_id])
    assignee = relationship(
        "User",
        back_populates="assigned_alerts",
        foreign_keys=[assigned_to],
    )

class User(Base):
    alerts = relationship(
        "Alert",
        back_populates="owner",
        foreign_keys="Alert.owner_id",
    )
    assigned_alerts = relationship(
        "Alert",
        back_populates="assignee",
        foreign_keys="Alert.assigned_to",
    )
```

### Testing expectations
- Mapper configuration should succeed without warnings or ambiguity errors.
- Basic CRUD tests should create a `User`, assign an `Alert` and `Incident`, and query
  relationships through both sides.
