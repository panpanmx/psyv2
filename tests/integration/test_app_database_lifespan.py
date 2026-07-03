from fastapi.testclient import TestClient

from app.main import create_app


def test_app_exposes_services_with_sessionmaker() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert hasattr(app.state.services, "sessionmaker")
