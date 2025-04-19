"""
Тестовый скрипт для проверки работы с заметками через MCP протокол.
"""

import asyncio
import websockets
import json
import uuid
import argparse
from datetime import datetime

async def test_notes():
    """Тестирование операций с заметками через MCP протокол."""
    uri = "ws://localhost:8080/mcp/ws"
    
    async with websockets.connect(uri) as websocket:
        # Аутентификация
        auth_message = {
            "id": str(uuid.uuid4()),
            "type": "auth",
            "content": {
                "token": "test_token"
            }
        }
        await websocket.send(json.dumps(auth_message))
        response = await websocket.recv()
        print("Auth response:", response)
        
        # Создание категории
        category_message = {
            "id": str(uuid.uuid4()),
            "type": "create_note_category",
            "content": {
                "name": args.category,
                "description": args.category_desc
            }
        }
        await websocket.send(json.dumps(category_message))
        response = await websocket.recv()
        print("Category creation response:", response)
        
        # Создание тега
        tag_message = {
            "id": str(uuid.uuid4()),
            "type": "create_tag",
            "content": {
                "name": args.tag,
                "description": args.tag_desc
            }
        }
        await websocket.send(json.dumps(tag_message))
        response = await websocket.recv()
        print("Tag creation response:", response)
        
        # Создание заметки
        note_message = {
            "id": str(uuid.uuid4()),
            "type": "create_note",
            "content": {
                "title": args.title,
                "content": args.content,
                "category": args.category,
                "status": args.status,
                "priority": args.priority,
                "tags": [args.tag],
                "session_id": args.session_id
            }
        }
        await websocket.send(json.dumps(note_message))
        response = await websocket.recv()
        print("Note creation response:", response)
        
        # Получение информации о созданной заметке
        response_data = json.loads(response)
        if response_data["type"] == "note_created":
            note_id = response_data["content"]["note_id"]
            get_note_message = {
                "id": str(uuid.uuid4()),
                "type": "get_note",
                "content": {
                    "note_id": note_id
                }
            }
            await websocket.send(json.dumps(get_note_message))
            response = await websocket.recv()
            print("Get note response:", response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Тестирование операций с заметками через MCP протокол')
    parser.add_argument('--title', type=str, default='Test Note', help='Заголовок заметки')
    parser.add_argument('--content', type=str, default='This is a test note', help='Содержимое заметки')
    parser.add_argument('--category', type=str, default='Test Category', help='Название категории')
    parser.add_argument('--category-desc', type=str, default='Test category description', help='Описание категории')
    parser.add_argument('--tag', type=str, default='Test Tag', help='Название тега')
    parser.add_argument('--tag-desc', type=str, default='Test tag description', help='Описание тега')
    parser.add_argument('--status', type=str, default='active', help='Статус заметки')
    parser.add_argument('--priority', type=int, default=0, help='Приоритет заметки')
    parser.add_argument('--session-id', type=str, default=None, help='ID сессии')
    
    args = parser.parse_args()
    asyncio.run(test_notes()) 