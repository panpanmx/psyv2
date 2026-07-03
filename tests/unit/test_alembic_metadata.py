from app.db import models as _models
from app.db.base import Base


def test_initial_metadata_contains_required_tables() -> None:
    _ = _models
    assert {
        "users",
        "conversations",
        "messages",
        "user_profiles",
        "assessments",
        "risk_assessments",
        "audit_logs",
    } <= set(Base.metadata.tables)
