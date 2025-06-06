# app/intent_handlers/math_operation_handler.py

import traceback  # Для вывода информации об ошибках


def handle_math_operation(entities: dict) -> dict:
    """
    Handles the 'math_operation' intent.
    Tries to evaluate the mathematical expression provided in entities.
    Returns a dictionary with the result or an error message.
    """
    print(f"MathOperationHandler: Received entities: {entities}")

    expression_to_evaluate = entities.get("expression")

    if not expression_to_evaluate:
        error_msg = "MathOperationHandler: No expression found in entities to evaluate."
        print(error_msg)
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": "Не удалось найти математическое выражение для вычисления.",
            "expression_evaluated": None,
            "result": None,
        }

    print(f"MathOperationHandler: Attempting to evaluate expression: '{expression_to_evaluate}'")

    try:
        # ВНИМАНИЕ: Использование eval() может быть небезопасным с неконтролируемым вводом.
        # Для нашего случая, где выражение приходит от NLU и в основном используется тобой,
        # риск приемлем на данном этапе.
        # В будущем можно рассмотреть более безопасные парсеры, если потребуется.

        # Простая проверка на наличие только разрешенных символов перед eval
        # Это очень базовая защита, не исчерпывающая!
        # Добавил % для остатка от деления
        allowed_chars = set("0123456789.+-*/%() ")
        if not all(char in allowed_chars for char in expression_to_evaluate):
            error_msg = f"MathOperationHandler: Expression '{expression_to_evaluate}' contains disallowed characters."
            print(error_msg)
            return {
                "success": False,
                "action_performed": "math_calculation_error",
                "details_or_error": "Выражение содержит недопустимые символы.",
                "expression_evaluated": expression_to_evaluate,
                "result": None,
            }

        # Для более сложных функций, таких как 'sqrt', 'sin', 'cos', 'pow',
        # нам нужно будет либо импортировать модуль math и разрешить их в eval,
        # либо написать свой парсер. Пока ограничимся базовой арифметикой.
        # Для 'в кубе' или 'в степени' NLU уже дает нам "25 ** 3", что eval поймет.

        calculation_result = eval(expression_to_evaluate)

        print(f"MathOperationHandler: Expression '{expression_to_evaluate}' evaluated to: {calculation_result}")

        # Попытаемся сделать результат более "красивым", если это float с .0 на конце
        if isinstance(calculation_result, float) and calculation_result.is_integer():
            calculation_result = int(calculation_result)

        return {
            "success": True,
            "action_performed": "math_calculation_success",
            "details_or_error": "Вычисление успешно выполнено.",
            "expression_evaluated": expression_to_evaluate,
            "result": calculation_result,
        }

    except ZeroDivisionError:
        error_msg = f"MathOperationHandler: Error evaluating expression '{expression_to_evaluate}': Division by zero."
        print(error_msg)
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": "Деление на ноль невозможно.",
            "error_type": "ZeroDivisionError",
            "expression_evaluated": expression_to_evaluate,
            "result": None,
        }
    except SyntaxError:
        error_msg = f"MathOperationHandler: Error evaluating expression '{expression_to_evaluate}': Syntax error."
        print(error_msg)
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": "Ошибка в синтаксисе математического выражения.",
            "error_type": "SyntaxError",
            "expression_evaluated": expression_to_evaluate,
            "result": None,
        }
    except Exception as e:
        error_msg = f"MathOperationHandler: Unexpected error evaluating expression '{expression_to_evaluate}': {e}"
        print(error_msg)
        traceback.print_exc()  # Выведем полный traceback для отладки
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": f"Произошла непредвиденная ошибка при вычислении: {e}",
            "error_type": type(e).__name__,
            "expression_evaluated": expression_to_evaluate,
            "result": None,
        }


if __name__ == "__main__":
    # Простые тесты для math_operation_handler
    test_entities = [
        {"expression": "2 + 2"},
        {"expression": "100 - (200 / 5)"},
        {"expression": "3 * 3 - 5"},
        {"expression": "2 ** 10"},
        {"expression": "10 / 0"},  # Ошибка деления на ноль
        {"expression": "10 /"},  # Синтаксическая ошибка
        # Недопустимые символы (базовая проверка)
        {"expression": "print('hello')"},
    ]

    for entities_case in test_entities:
        print(f"\n--- Testing math_operation_handler with entities: {entities_case} ---")
        result = handle_math_operation(entities_case)
        print(f"Result from handler: {result}")
