# calculator_server.py
import logging

# Импортируем основной класс для создания сервера из SDK
from mcp.server.fastmcp import FastMCP

# Настраиваем базовое логирование для отладки.
# Логи будут показывать, что происходит внутри сервера.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - SERVER - %(message)s')

# 1. Создаем экземпляр сервера с уникальным именем.
# Это имя будет видно в клиентских приложениях.
mcp = FastMCP("CalculatorServer")

# 2. Используем декоратор @mcp.tool() для регистрации функции как инструмента MCP.
# SDK автоматически анализирует аннотации типов (a: int, b: int) и возвращаемое
# значение (-> int) для генерации JSON Schema для этого инструмента.
# Строка документации (docstring) используется как описание инструмента,
# которое LLM будет использовать для принятия решения о его вызове.
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Вычисляет сумму двух целых чисел. Этот инструмент полезен для
    любых арифметических операций сложения.
    :param a: Первое слагаемое.
    :param b: Второе слагаемое.
    :return: Целочисленная сумма a и b.
    """
    logging.info(f"Выполняется инструмент 'add' с аргументами: a={a}, b={b}")
    result = a + b
    logging.info(f"Возвращается результат: {result}")
    return result

# 3. Блок для запуска сервера, если скрипт выполняется напрямую.
# mcp.run() запускает сервер. По умолчанию используется транспорт 'stdio',
# что идеально для локального тестирования.
if __name__ == "__main__":
    logging.info("Запуск MCP-сервера 'Калькулятор'...")
    mcp.run(transport="stdio")