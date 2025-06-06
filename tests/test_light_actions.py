import importlib
import os
import sys
from unittest import mock

import pytest

# Ensure project root is in sys.path for module resolution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the light_actions module fresh to ensure config loading runs
light_actions = importlib.import_module('app.actions.light_actions')


@pytest.fixture(autouse=True)
def fake_config(monkeypatch):
    """Provide fake Home Assistant configuration for tests."""
    monkeypatch.setattr(light_actions, "HA_URL", "http://ha.test")
    monkeypatch.setattr(light_actions, "HA_TOKEN", "TOKEN")
    monkeypatch.setattr(light_actions, "DEFAULT_LIGHT_ENTITY_IDS", ["light.test1"])


@pytest.fixture
def mock_post(monkeypatch):
    """Mock requests.post used by light_actions."""
    mock_response = mock.Mock(status_code=200, text="ok")
    mock_response.raise_for_status = mock.Mock()
    post_mock = mock.Mock(return_value=mock_response)
    monkeypatch.setattr(light_actions.requests, "post", post_mock)
    return post_mock


def test_turn_on_invalid_brightness_low():
    result = light_actions.turn_on(brightness_percent=-1)
    assert result["success"] is False
    assert "Яркость" in result.get("error", "")


def test_turn_on_invalid_brightness_high():
    result = light_actions.turn_on(brightness_percent=101)
    assert result["success"] is False
    assert "Яркость" in result.get("error", "")


def test_set_color_temperature_invalid_string():
    result = light_actions.set_color_temperature("hot")
    assert result["success"] is False
    assert "Неизвестное значение" in result.get("error", "")


def test_set_color_temperature_invalid_numeric():
    result = light_actions.set_color_temperature(900)
    assert result["success"] is False
    assert "температуры" in result.get("error", "")


def test_turn_on_calls_correct_endpoint(mock_post):
    result = light_actions.turn_on(entity_ids=["light.custom"], brightness_percent=75)
    assert result["success"] is True
    expected_url = "http://ha.test/api/services/light/turn_on"
    expected_headers = {
        "Authorization": "Bearer TOKEN",
        "Content-Type": "application/json",
    }
    expected_payload = {"entity_id": "light.custom", "brightness_pct": 75}
    mock_post.assert_called_once_with(
        expected_url, headers=expected_headers, json=expected_payload, timeout=10
    )


def test_turn_off_calls_correct_endpoint_with_default(mock_post):
    result = light_actions.turn_off()
    assert result["success"] is True
    expected_url = "http://ha.test/api/services/light/turn_off"
    expected_headers = {
        "Authorization": "Bearer TOKEN",
        "Content-Type": "application/json",
    }
    expected_payload = {"entity_id": "light.test1"}
    mock_post.assert_called_once_with(
        expected_url, headers=expected_headers, json=expected_payload, timeout=10
    )
