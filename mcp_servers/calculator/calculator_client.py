# calculator_client.py
import asyncio
import logging

# Импортируем необходимые классы для создания клиента
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Настраиваем логирование для клиента
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CLIENT - %(message)s')

async def main():
    """
    Основная асинхронная функция для запуска клиента, подключения к серверу
    и вызова инструмента.
    """
    logging.info("Инициализация MCP-клиента...")

    # 1. Определяем параметры для запуска нашего локального сервера.
    # Указываем, что нужно запустить интерпретатор 'python' и передать
    # ему в качестве аргумента наш скрипт 'calculator_server.py'.
    server_params = StdioServerParameters(
        command="python",
        args=["calculator_server.py"],
    )

    # 2. Используем 'stdio_client' как асинхронный контекстный менеджер.
    # Он автоматически запускает серверный процесс и предоставляет
    # асинхронные потоки для чтения (read) и записи (write).
    async with stdio_client(server_params) as (read, write):
        logging.info("Серверный процесс запущен. Установка сессии...")

        # 3. 'ClientSession' - это высокоуровневый менеджер MCP-соединения.
        # Он обертывает потоки чтения/записи и управляет жизненным циклом сессии.
        async with ClientSession(read, write) as session:
            # Обязательный первый шаг: 'рукопожатие' с сервером.
            await session.initialize()
            logging.info("Сессия успешно инициализирована.")

            # 4. Динамическое обнаружение инструментов.
            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            logging.info(f"Обнаружены инструменты на сервере: {tool_names}")

            if "add" in tool_names:
                # 5. Вызов инструмента 'add' с конкретными аргументами.
                a, b = 5, 7
                logging.info(f"Вызов инструмента 'add' с a={a}, b={b}...")
                call_result = await session.call_tool(
                    name="add",
                    arguments={"a": a, "b": b}
                )

                # 6. Обработка результата.
                if not call_result.isError and call_result.content:
                    # ИСПРАВЛЕНИЕ: Результат приходит в виде списка. Берем первый элемент.
                    result_text = call_result.content[0].text
                    logging.info(f"Сервер ответил с результатом: {result_text}")
                    # Простая проверка, что результат корректен
                    assert int(result_text) == a + b
                    logging.info("Проверка пройдена: результат верный.")
                else:
                    error_text = call_result.content[0].text if call_result.content else "Неизвестная ошибка"
                    logging.error(f"Вызов инструмента не удался: {error_text}")
            else:
                logging.error("Критическая ошибка: инструмент 'add' не найден на сервере.")

if __name__ == "__main__":
    # Запускаем асинхронную функцию main.
    asyncio.run(main())
