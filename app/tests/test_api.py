import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch.dict(os.environ, {"AGENT_SERVER_URL": "http://fake-server"})
@patch("main.list_agents", new_callable=AsyncMock)
@patch("main.create_session", new_callable=AsyncMock)
@patch("main.query_adk_server")
def test_chat_stream_missing_config(
    mock_query, mock_create_session, mock_list_agents, client
):
    # Temporarily remove AGENT_SERVER_URL from env for this test
    with patch.dict(os.environ, {}, clear=True):
        import main

        main.agent_server_url = None
        response = client.post(
            "/api/chat_stream", json={"message": "test", "user_id": "user1"}
        )
        assert response.status_code == 200
        assert "error" in response.json()
        assert (
            "AGENT_SERVER_URL environment variable not set" in response.json()["error"]
        )


@patch.dict(os.environ, {"AGENT_SERVER_URL": "http://fake-server"})
@patch("main.list_agents", new_callable=AsyncMock)
@patch("main.create_session", new_callable=AsyncMock)
@patch("main.query_adk_server")
def test_chat_stream_success(mock_query, mock_create_session, mock_list_agents, client):
    import main

    main.agent_server_url = "http://fake-server"

    mock_list_agents.return_value = ["agent"]
    mock_create_session.return_value = {"id": "session1"}

    # Mock the query_adk_server async generator
    async def mock_events(*args, **kwargs):
        yield {
            "author": "researcher",
            "content": {"parts": [{"text": "Researching..."}]},
        }
        yield {
            "author": "content_builder",
            "content": {"parts": [{"text": "Course content."}]},
        }

    mock_query.side_effect = mock_events

    response = client.post(
        "/api/chat_stream", json={"message": "test", "user_id": "user1"}
    )
    assert response.status_code == 200

    # Check if the response is an NDJSON stream
    lines = response.text.strip().split("\n")
    assert len(lines) > 0

    import json

    data = [json.loads(line) for line in lines]

    # Check for progress and result types
    types = [d["type"] for d in data]
    assert "progress" in types
    assert "result" in types

    # Find result
    result = next(d for d in data if d["type"] == "result")
    assert result["text"] == "Course content."
