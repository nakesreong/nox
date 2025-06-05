import importlib
import os
import sys

import pytest

# Ensure project root is in sys.path for module resolution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the light_actions module fresh to ensure config loading runs
light_actions = importlib.import_module('app.actions.light_actions')


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
