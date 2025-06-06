import importlib
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

math_handler = importlib.import_module('app.intent_handlers.math_operation_handler')


def test_valid_expression_addition():
    result = math_handler.handle_math_operation({'expression': '2 + 3 * 4'})
    assert result['success'] is True
    assert result['result'] == 14


def test_valid_expression_integer_conversion():
    result = math_handler.handle_math_operation({'expression': '6 / 3'})
    assert result['success'] is True
    assert result['result'] == 2


def test_disallowed_characters():
    result = math_handler.handle_math_operation({'expression': '2 + two'})
    assert result['success'] is False
    assert 'disallowed characters' in result['details_or_error'].lower()


def test_zero_division_error():
    result = math_handler.handle_math_operation({'expression': '10 / 0'})
    assert result['success'] is False
    assert result.get('error_type') == 'ZeroDivisionError'


def test_syntax_error():
    result = math_handler.handle_math_operation({'expression': '10 /'})
    assert result['success'] is False
    assert result.get('error_type') == 'SyntaxError'


def test_missing_expression():
    result = math_handler.handle_math_operation({})
    assert result['success'] is False
    assert result['action_performed'] == 'math_calculation_error'
