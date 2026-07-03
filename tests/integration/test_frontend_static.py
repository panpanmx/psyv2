from fastapi.testclient import TestClient

from app.main import create_app


def test_home_page_serves_frontend_shell() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<main class="app-shell"' in response.text
    assert "/static/styles.css" in response.text
    assert "/static/app.js" in response.text


def test_frontend_static_assets_are_served() -> None:
    client = TestClient(create_app())

    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert ".app-shell" in css_response.text
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert "sendMessage" in js_response.text
