import importlib
from unittest import mock
import pytest


@pytest.fixture(scope="module")
def handler(add_project_root_to_sys_path):
    return importlib.import_module('app.intent_handlers.device_control_handler')


@pytest.fixture(scope="module")
def light_actions(add_project_root_to_sys_path):
    return importlib.import_module('app.actions.light_actions')


def test_turn_on_calls_light_actions(monkeypatch, handler, light_actions):
    mock_turn_on = mock.Mock(return_value={'success': True, 'message': 'ok'})
    monkeypatch.setattr(light_actions, 'turn_on', mock_turn_on)
    result = handler.handle_device_control({'target_device': 'light', 'action': 'turn_on'})
    mock_turn_on.assert_called_once_with()
    assert result['success'] is True
    assert result['action_performed'] == 'turn_on'


def test_setting_brightness_and_kelvin(monkeypatch, handler, light_actions):
    mock_turn_on = mock.Mock(return_value={'success': True, 'message': 'ok'})
    monkeypatch.setattr(light_actions, 'turn_on', mock_turn_on)
    entities = {
        'target_device': 'light',
        'action': 'setting',
        'brightness_pct': 50,
        'color_temp_kelvin': 4000,
    }
    result = handler.handle_device_control(entities)
    mock_turn_on.assert_called_once_with(brightness_percent=50, kelvin=4000)
    assert result['brightness_pct_set'] == 50
    assert result['color_temp_kelvin_set'] == 4000


def test_setting_qualitative_temperature(monkeypatch, handler, light_actions):
    mock_turn_on = mock.Mock(return_value={'success': True, 'message': 'ok'})
    monkeypatch.setattr(light_actions, 'turn_on', mock_turn_on)
    entities = {'target_device': 'light', 'action': 'setting', 'color_temp_qualitative': 'warm'}
    result = handler.handle_device_control(entities)
    mock_turn_on.assert_called_once_with(brightness_percent=None, kelvin=2700)
    assert result['color_temp_qualitative_set'] == 'warm'
    assert result['color_temp_kelvin_set'] == 2700


def test_setting_invalid_temperature(monkeypatch, handler, light_actions):
    mock_turn_on = mock.Mock(return_value={'success': True, 'message': 'ok'})
    monkeypatch.setattr(light_actions, 'turn_on', mock_turn_on)
    entities = {'target_device': 'light', 'action': 'setting', 'color_temp_qualitative': 'invalid'}
    result = handler.handle_device_control(entities)
    mock_turn_on.assert_not_called()
    assert result['success'] is False
    assert 'Unknown qualitative temperature' in result['details_or_error']


def test_unknown_target_device(monkeypatch, handler, light_actions):
    mock_turn_on = mock.Mock(return_value={'success': True, 'message': 'ok'})
    monkeypatch.setattr(light_actions, 'turn_on', mock_turn_on)
    result = handler.handle_device_control({'target_device': 'fan', 'action': 'turn_on'})
    mock_turn_on.assert_not_called()
    assert result['success'] is False
    assert result['action_performed'] == 'unknown_target_device'


def test_unknown_light_action(monkeypatch, handler, light_actions):
    mock_turn_on = mock.Mock(return_value={'success': True, 'message': 'ok'})
    monkeypatch.setattr(light_actions, 'turn_on', mock_turn_on)
    entities = {'target_device': 'light', 'action': 'blink'}
    result = handler.handle_device_control(entities)
    mock_turn_on.assert_not_called()
    assert result['success'] is False
    assert result['action_performed'] == 'unknown_light_action'

