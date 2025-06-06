from app.intent_handlers.math_operation_handler import handle_math_operation

# Simple tests for math_operation_handler
test_entities = [
    {"expression": "2 + 2"},
    {"expression": "100 - (200 / 5)"},
    {"expression": "3 * 3 - 5"},
    {"expression": "2 ** 10"},
    {"expression": "10 / 0"},  # Division by zero error
    {"expression": "10 /"},  # Syntax error
    {"expression": "print('hello')"},  # Disallowed characters
]

for entities_case in test_entities:
    print(f"\n--- Testing math_operation_handler with entities: {entities_case} ---")
    result = handle_math_operation(entities_case)
    print(f"Result from handler: {result}")
