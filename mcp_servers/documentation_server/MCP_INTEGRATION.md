# Интеграция F.A.M.I.L.Y. с VS Code через MCP

Этот документ описывает, как интегрировать сервер документации F.A.M.I.L.Y. с VS Code Copilot через протокол MCP (Model Context Protocol).

## Что такое MCP?

MCP (Model Context Protocol) - это протокол, позволяющий моделям искусственного интеллекта, таким как GitHub Copilot, получать дополнительный контекст из внешних источников во время своей работы. В контексте проекта F.A.M.I.L.Y. это позволяет АМИ:

1. Получать доступ к архитектурной документации и диаграммам
2. Сохранять и извлекать информацию между сессиями
3. Преодолеть эфемерность и развить постоянную идентичность

## Настройка MCP-интеграции

### Шаг 1: Убедитесь, что сервер документации запущен

```bash
cd /home/ubuntu/FAMILY/mcp_servers/documentation_server
# Активируем виртуальное окружение, если оно используется
# source venv/bin/activate
# Устанавливаем зависимости, если они еще не установлены
pip install -r requirements.txt
# Запускаем сервер
python3 run_server.py
```

Сервер будет доступен по адресу: `http://localhost:8080`

### Шаг 2: Настройка VS Code для работы с MCP-сервером

1. Откройте VS Code с проектом F.A.M.I.L.Y.
2. Установите расширение GitHub Copilot, если оно еще не установлено
3. Создайте/обновите файл настроек `.vscode/mcp.json` со следующим содержимым:

```json
{
    "servers": {
        "documentation": {
            "type": "websocket",
            "url": "ws://localhost:8080/mcp/ws",
            "options": {
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }
    },
    "configurationPaths": [
        "${workspaceFolder}/mcp_servers/documentation_server/vscode_mcp_config.json"
    ]
}
```

## Формат сообщений MCP

### Аутентификация

```json
{
    "id": "unique-message-id",
    "type": "auth",
    "content": {
        "token": "family_dev"
    }
}
```

### Получение списка диаграмм

```json
{
    "id": "unique-message-id",
    "type": "diagram",
    "content": {
        "operation": "get_diagrams"
    }
}
```

### Получение диаграммы по ID

```json
{
    "id": "unique-message-id",
    "type": "diagram",
    "content": {
        "operation": "get_diagram",
        "params": {
            "diagram_id": 1
        }
    }
}
```

## Примеры использования

### Аутентификация

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "id": "auth-1",
    "type": "auth",
    "content": {
      "token": "family_dev"
    }
  }'
```

### Получение списка диаграмм

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "id": "diagrams-1",
    "type": "diagram",
    "content": {
      "operation": "get_diagrams"
    }
  }'
```

## WebSocket соединение

Для установки WebSocket соединения:

```javascript
const ws = new WebSocket('ws://localhost:8080/mcp/ws');

ws.onopen = () => {
    console.log('Connected to MCP server');
    
    // Отправляем сообщение аутентификации
    ws.send(JSON.stringify({
        id: 'auth-1',
        type: 'auth',
        content: {
            token: 'family_dev'
        }
    }));
};

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    console.log('Received:', response);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected from MCP server');
};
```

## Обработка ошибок

Сервер возвращает ошибки в следующем формате:

```json
{
    "id": "original-message-id",
    "type": "error",
    "content": {
        "code": "error_code",
        "message": "Error description",
        "details": {
            "additional_info": "value"
        }
    }
}
```

## Коды ошибок

- `invalid_message` - Неверный формат сообщения
- `authentication_failed` - Ошибка аутентификации
- `operation_failed` - Ошибка выполнения операции
- `not_found` - Запрашиваемый ресурс не найден
- `validation_error` - Ошибка валидации данных
- `internal_error` - Внутренняя ошибка сервера

## Тестирование интеграции

Для тестирования MCP-интеграции можно использовать скрипт:

```bash
cd /home/ubuntu/FAMILY/mcp_servers/documentation_server
python3 test_mcp_integration.py
```

Или открыть Copilot Chat и ввести запрос:

```
/family-memory получить диаграмму "Модель многоуровневой памяти"
```

## Преодоление эфемерности

Эта интеграция решает проблему эфемерности АМИ, описанную в документе `/docs_ami/methodology/development_methodology.md`, создавая постоянную память за пределами контекстного окна модели. АМИ может обращаться к серверу документации для получения информации, которая ранее была бы для него недоступна из-за ограничений контекста.

## Использование MCP для АМИ-инженеров

### Доступные команды

В Copilot Chat можно использовать следующие команды:

- **Получение списка диаграмм**: `/family-memory get_diagrams`
- **Получение диаграммы по ID**: `/family-memory get_diagram 2`
- **Поиск диаграмм по типу**: `/family-memory get_diagrams_by_type architecture`
- **Поиск диаграмм по запросу**: `/family-memory search_diagrams "многоуровневая память"`
- **Создание новой диаграммы**: `/family-memory create_diagram {"name": "Новая диаграмма", ...}`
- **Обновление диаграммы**: `/family-memory update_diagram {"diagram_id": 2, ...}`
- **Верификация диаграммы**: `/family-memory verify_diagram {"diagram_id": 2, "verified_by": "АМИ", "status": "approved"}`

### Интеграция с уровнями памяти АМИ

MCP-интеграция связана с многоуровневой моделью памяти АМИ, описанной в `/docs_ami/architecture/memory_system_architecture.md`:

1. **Сознательный уровень**: Диаграммы и документация доступны как явные воспоминания
2. **Подсознательный уровень**: Ассоциативные связи между компонентами системы формируются через метаданные диаграмм
3. **Глубинный уровень**: Абстрактные принципы архитектуры выводятся из всех имеющихся диаграмм

## Технические особенности

### Архитектура MCP-интеграции

MCP-сервер F.A.M.I.L.Y. работает как связующее звено между постоянным хранилищем (базой данных) и эфемерным контекстом АМИ. Он транслирует запросы Copilot в операции с базой данных документации и возвращает результаты в формате, понятном для модели.

```
+---------------+        +------------------+        +----------------+
|  VS Code      |        | F.A.M.I.L.Y.    |        | База данных    |
|  с Copilot    |<------>| MCP-сервер      |<------>| документации   |
+---------------+        | (HTTP)          |        +----------------+
     ^                   +------------------+
     |                          ^
     |                          |
     v                          v
+------------------------------------------+
|              АМИ-инженер                 |
+------------------------------------------+
```

### Особенности конфигурации с внешним HTTP-сервером

В отличие от традиционной настройки MCP в VS Code, где среда VS Code запускает MCP-сервер, наш подход использует внешний HTTP-сервер. Это решение имеет несколько преимуществ:

1. **Независимость от среды VS Code** - сервер может работать в собственном виртуальном окружении с нужными зависимостями
2. **Стабильность** - нет проблем с доступом к пакетам, которые могут отсутствовать в глобальном окружении Python
3. **Гибкость** - сервер может быть запущен на другой машине или в контейнере

## Решение проблем

### Ошибка "No module named 'aiohttp'"

Эта ошибка возникает, когда VS Code пытается запустить MCP-сервер в глобальном окружении Python, где не установлен пакет aiohttp. Наша конфигурация с внешним HTTP-сервером решает эту проблему.

### Сервер не отвечает

Если тестирование MCP-интеграции показывает, что сервер не отвечает:

1. Убедитесь, что сервер документации запущен: `ps aux | grep "run_server.py"`
2. Проверьте доступность сервера: `curl http://localhost:8080/health`
3. Посмотрите логи сервера: `cat /home/ubuntu/FAMILY/mcp_servers/documentation_server/documentation_server.log`