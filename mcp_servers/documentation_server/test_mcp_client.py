import asyncio
import websockets
import json
import logging
import uuid

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    uri = "ws://localhost:8080/mcp/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Успешно подключились к WebSocket серверу")
            
            # Тест аутентификации
            auth_message = {
                "id": str(uuid.uuid4()),
                "type": "auth",
                "content": {
                    "token": "family_dev"
                }
            }
            
            logger.info("Отправляем сообщение аутентификации...")
            await websocket.send(json.dumps(auth_message))
            
            response = await websocket.recv()
            logger.info(f"Получен ответ на аутентификацию: {response}")
            
            # Тест запроса списка диаграмм
            diagrams_request = {
                "id": str(uuid.uuid4()),
                "type": "diagram",
                "content": {
                    "operation": "get_diagrams"
                }
            }
            
            logger.info("Отправляем запрос списка диаграмм...")
            await websocket.send(json.dumps(diagrams_request))
            
            response = await websocket.recv()
            logger.info(f"Получен список диаграмм: {response}")
            
            # Тест запроса конкретной диаграммы
            diagram_request = {
                "id": str(uuid.uuid4()),
                "type": "diagram",
                "content": {
                    "operation": "get_diagram",
                    "params": {
                        "diagram_id": 2  # Запрашиваем диаграмму "Модель многоуровневой памяти"
                    }
                }
            }
            
            logger.info("Отправляем запрос конкретной диаграммы...")
            await websocket.send(json.dumps(diagram_request))
            
            response = await websocket.recv()
            logger.info(f"Получена диаграмма: {response}")
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection()) 