# app/intent_handlers/math_operation_handler.py

import traceback  # For error details


def handle_math_operation(entities: dict) -> dict:
    """Evaluate a math expression for the intent and return a result. Uses eval() on sanitized input; caution advised."""
    print(f"MathOperationHandler: Received entities: {entities}")

    expression_to_evaluate = entities.get("expression")

    if not expression_to_evaluate:
        error_msg = "MathOperationHandler: No expression found in entities to evaluate."
        print(error_msg)
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": "Could not find a math expression to evaluate.",
            "expression_evaluated": None,
            "result": None,
        }

    print(f"MathOperationHandler: Attempting to evaluate expression: '{expression_to_evaluate}'")

    try:

        # Basic check to allow only certain characters before eval
        # This is a minimal safeguard!
        # Added % for modulo operations
        allowed_chars = set("0123456789.+-*/%() ")
        if not all(char in allowed_chars for char in expression_to_evaluate):
            error_msg = f"MathOperationHandler: Expression '{expression_to_evaluate}' contains disallowed characters."
            print(error_msg)
            return {
                "success": False,
                "action_performed": "math_calculation_error",
                "details_or_error": "Expression contains disallowed characters.",
                "expression_evaluated": expression_to_evaluate,
                "result": None,
            }

        # For functions like 'sqrt', 'sin', 'cos', 'pow' we'd need to import math
        # and allow them in eval or write our own parser. For now only basic arithmetic.
        # For "to the power of" NLU already provides "25 ** 3" which eval understands.

        calculation_result = eval(expression_to_evaluate)

        print(f"MathOperationHandler: Expression '{expression_to_evaluate}' evaluated to: {calculation_result}")

        # Make the result nicer if it's a float ending with .0
        if isinstance(calculation_result, float) and calculation_result.is_integer():
            calculation_result = int(calculation_result)

        return {
            "success": True,
            "action_performed": "math_calculation_success",
            "details_or_error": "Calculation completed successfully.",
            "expression_evaluated": expression_to_evaluate,
            "result": calculation_result,
        }

    except ZeroDivisionError:
        error_msg = f"MathOperationHandler: Error evaluating expression '{expression_to_evaluate}': Division by zero."
        print(error_msg)
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": "Division by zero is not allowed.",
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
            "details_or_error": "Syntax error in math expression.",
            "error_type": "SyntaxError",
            "expression_evaluated": expression_to_evaluate,
            "result": None,
        }
    except Exception as e:
        error_msg = f"MathOperationHandler: Unexpected error evaluating expression '{expression_to_evaluate}': {e}"
        print(error_msg)
        traceback.print_exc()  # Print full traceback for debugging
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": f"Unexpected error during calculation: {e}",
            "error_type": type(e).__name__,
            "expression_evaluated": expression_to_evaluate,
            "result": None,
        }

# Manual test example: run this module directly to test math operations.
if __name__ == "__main__":
    # Simple tests for math_operation_handler
    test_entities = [
        {"expression": "2 + 2"},
        {"expression": "100 - (200 / 5)"},
        {"expression": "3 * 3 - 5"},
        {"expression": "2 ** 10"},
        {"expression": "10 / 0"},  # Division by zero error
        {"expression": "10 /"},  # Syntax error
        # Disallowed characters (basic check)
        {"expression": "print('hello')"},
    ]

    for entities_case in test_entities:
        print(f"\n--- Testing math_operation_handler with entities: {entities_case} ---")
        result = handle_math_operation(entities_case)
        print(f"Result from handler: {result}")
