import importlib
import pytest


@pytest.fixture(scope="module")
def math_handler(add_project_root_to_sys_path):
    return importlib.import_module('app.intent_handlers.math_operation_handler')


def test_valid_expression_addition(math_handler):
    result = math_handler.handle_math_operation({'expression': '2 + 3 * 4'})
    assert result['success'] is True
    assert result['result'] == 14


def test_valid_expression_integer_conversion(math_handler):
    result = math_handler.handle_math_operation({'expression': '6 / 3'})
    assert result['success'] is True
    assert result['result'] == 2


def test_disallowed_variable(math_handler):
    result = math_handler.handle_math_operation({'expression': '2 + two'})
    assert result['success'] is False
    assert 'disallowed' in result['details_or_error'].lower()


def test_disallowed_function_call(math_handler):
    result = math_handler.handle_math_operation({'expression': 'abs(5)'})
    assert result['success'] is False
    assert 'disallowed' in result['details_or_error'].lower()


def test_zero_division_error(math_handler):
    result = math_handler.handle_math_operation({'expression': '10 / 0'})
    assert result['success'] is False
    assert result.get('error_type') == 'ZeroDivisionError'


def test_syntax_error(math_handler):
    result = math_handler.handle_math_operation({'expression': '10 /'})
    assert result['success'] is False
    assert result.get('error_type') == 'SyntaxError'


def test_missing_expression(math_handler):
    result = math_handler.handle_math_operation({})
    assert result['success'] is False
    assert result['action_performed'] == 'math_calculation_error'

