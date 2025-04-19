from aiohttp import web
import json

async def get_help(request):
    """
    Возвращает базовую документацию по использованию MCP сервера.
    """
    help_info = {
        "title": "MCP Documentation Server Help",
        "description": "Этот сервер предоставляет API для работы с документацией через MCP протокол",
        "endpoints": {
            "/health": "Проверка работоспособности сервера",
            "/mcp/ws": "WebSocket endpoint для MCP протокола",
            "/help": "Эта страница с документацией"
        },
        "mcp_protocol": {
            "connection": "ws://localhost:8080/mcp/ws",
            "authentication": {
                "message": {
                    "type": "auth",
                    "content": {
                        "token": "your_token"
                    }
                }
            },
            "basic_operations": {
                "create_note": {
                    "type": "create_note",
                    "content": {
                        "title": "Заголовок заметки",
                        "content": "Содержимое заметки",
                        "category": "Категория",
                        "status": "active",
                        "priority": 0,
                        "tags": ["тег1", "тег2"]
                    }
                },
                "get_note": {
                    "type": "get_note",
                    "content": {
                        "note_id": 1
                    }
                },
                "search_notes": {
                    "type": "search_notes",
                    "content": {
                        "query": "текст для поиска",
                        "category": "категория",
                        "tags": ["тег1"]
                    }
                }
            }
        },
        "examples": {
            "python": {
                "websocket_client": "import websockets\nimport json\n\nasync def connect():\n    async with websockets.connect('ws://localhost:8080/mcp/ws') as ws:\n        # Аутентификация\n        await ws.send(json.dumps({\n            'type': 'auth',\n            'content': {'token': 'test_token'}\n        }))\n        response = await ws.recv()\n        print(response)\n\n        # Создание заметки\n        await ws.send(json.dumps({\n            'type': 'create_note',\n            'content': {\n                'title': 'Тестовая заметка',\n                'content': 'Содержимое заметки',\n                'category': 'Тест',\n                'status': 'active',\n                'priority': 0,\n                'tags': ['тест']\n            }\n        }))\n        response = await ws.recv()\n        print(response)"
            }
        }
    }
    
    return web.Response(
        text=json.dumps(help_info, indent=2, ensure_ascii=False),
        content_type='application/json'
    ) 