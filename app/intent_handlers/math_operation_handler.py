# app/intent_handlers/math_operation_handler.py

import traceback  # For error details
import ast
import operator


# Allowed operators mapping for safe evaluation
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}


def _eval_ast(node):
    """Recursively evaluate an AST node containing only arithmetic."""
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")
    elif isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _OPERATORS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _eval_ast(node.operand)
        return +operand if isinstance(node.op, ast.UAdd) else -operand
    else:
        raise ValueError("Expression contains disallowed operations")


def handle_math_operation(entities: dict) -> dict:
    """Evaluate a math expression for the intent and return a result using safe AST evaluation."""
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
        parsed = ast.parse(expression_to_evaluate, mode="eval")
        calculation_result = _eval_ast(parsed)

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
    except ValueError as ve:
        error_msg = (
            f"MathOperationHandler: Expression '{expression_to_evaluate}' contains disallowed operations."
        )
        print(error_msg)
        return {
            "success": False,
            "action_performed": "math_calculation_error",
            "details_or_error": "Expression contains disallowed characters or operations.",
            "error_type": type(ve).__name__,
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

