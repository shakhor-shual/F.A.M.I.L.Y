import json
import logging
import asyncio
from aiohttp import web
from datetime import datetime

logger = logging.getLogger(__name__)

class SSEHandler:
    """Обработчик Server-Sent Events"""
    
    def __init__(self):
        self.clients = set()
        self.keep_alive_interval = 30  # seconds
    
    async def handle_sse(self, request):
        """Обрабатывает SSE соединение"""
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
        # Отправляем заголовки
        await response.prepare(request)
        
        # Добавляем клиента в список
        self.clients.add(response)
        
        try:
            # Отправляем событие подключения
            await self._send_event(response, 'connected', {'status': 'ok', 'message': 'Connected to SSE server'})
            
            # Отправляем keep-alive сообщения
            while True:
                await asyncio.sleep(self.keep_alive_interval)
                if response in self.clients:
                    await self._send_event(response, 'ping', {'timestamp': datetime.now().isoformat()})
                else:
                    break
                    
        except Exception as e:
            logger.error(f"Error in SSE connection: {e}")
        finally:
            # Удаляем клиента из списка
            self.clients.discard(response)
            
        return response
    
    async def _send_event(self, response, event_type, data):
        """Отправляет SSE событие"""
        try:
            if response in self.clients:
                await response.write(f"event: {event_type}\n".encode())
                await response.write(f"data: {json.dumps(data)}\n\n".encode())
                await response.drain()
        except Exception as e:
            logger.error(f"Error sending SSE event: {e}")
            self.clients.discard(response)
    
    async def broadcast(self, event_type, data):
        """Отправляет событие всем подключенным клиентам"""
        for client in list(self.clients):
            await self._send_event(client, event_type, data)

    async def send_note_event(self, note_data):
        """Отправляет событие о создании/обновлении заметки"""
        await self.broadcast('note', {
            'jsonrpc': '2.0',
            'method': 'note',
            'params': note_data
        })

    async def send_category_event(self, category_data):
        """Отправляет событие о создании/обновлении категории"""
        await self.broadcast('category', {
            'jsonrpc': '2.0',
            'method': 'category',
            'params': category_data
        })

    async def send_tag_event(self, tag_data):
        """Отправляет событие о создании/обновлении тега"""
        await self.broadcast('tag', {
            'jsonrpc': '2.0',
            'method': 'tag',
            'params': tag_data
        }) 