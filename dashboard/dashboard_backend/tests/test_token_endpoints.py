import pytest

# Importing the app pulls in dashboard_db, which requires VIEWER_DB_URL.
fastapi_testclient = pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient  # noqa: E402

from dashboard_app_be import app  # noqa: E402

client = TestClient(app)

TOKEN_KEYS = {"input_tokens", "output_tokens", "thinking_tokens"}


def test_token_aggregates_returns_200_and_shape():
    resp = client.get("/documents/token_aggregates")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "error" not in body
    for model_name, totals in body.items():
        assert isinstance(model_name, str)
        assert set(totals.keys()) == TOKEN_KEYS
        for v in totals.values():
            assert isinstance(v, int)
