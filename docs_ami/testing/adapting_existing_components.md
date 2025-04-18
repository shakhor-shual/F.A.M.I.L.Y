# Руководство по адаптации существующих компонентов к интеграционному подходу тестирования

## Введение

Этот документ создан для адаптации существующих компонентов проекта F.A.M.I.L.Y. к философии "прорастающего дерева" и интеграционно-ориентированному подходу к тестированию. Руководство предназначено для АМИ-инженеров, которым необходимо модифицировать существующий код с учетом новых принципов разработки.

## Проблема эфемерности существующих компонентов

Многие существующие компоненты в проекте F.A.M.I.L.Y. могут быть подобны "ветвям, выросшим из воздуха" - они функциональны в изоляции, но недостаточно интегрированы с основной системой. Это приводит к тому, что при работе с этими компонентами АМИ-инженер не получает контекстных подсказок о том, как данный компонент связан с другими элементами системы.

## Процесс адаптации существующих компонентов

### 1. Анализ существующего компонента

**Шаг 1.1: Идентификация компонента**
- Определите четкие границы компонента: какие классы, функции, методы он включает
- Установите его текущую роль в системе
- Поймите его основные входные и выходные данные

**Шаг 1.2: Идентификация связей**
- С какими другими компонентами системы он должен взаимодействовать
- Какие данные он получает от других компонентов 
- Какие данные он предоставляет другим компонентам

### 2. Разработка интеграционных тестов для существующего компонента

**Шаг 2.1: Создание первого интеграционного теста**

Создайте тест, который показывает, как компонент интегрируется с существующей системой:

```python
@pytest.mark.integration
def test_existing_component_integration(db_session_postgres):
    # Получение зависимостей из общей системы
    dependency_service = get_dependency_service(db_session_postgres)
    
    # Создание экземпляра существующего компонента
    existing_component = ExistingComponent()
    
    # Демонстрация взаимодействия с системой
    result = existing_component.process_with_dependency(dependency_service)
    
    # Проверка корректности взаимодействия
    assert result.status == "success"
```

**Шаг 2.2: Идентификация несоответствий**

При написании этого интеграционного теста вы можете обнаружить, что существующий компонент:
- Не имеет чёткого интерфейса для взаимодействия с другими частями системы
- Использует собственные настройки/сервисы вместо общесистемных
- Не следует общим паттернам обработки данных

### 3. Рефакторинг для "прорастания" компонента в систему

**Шаг 3.1: Стандартизация интерфейсов**

```python
# СТАРЫЙ КОД: Изолированный компонент
class ExistingComponent:
    def __init__(self):
        self.custom_db = CustomDbConnection()  # собственное подключение
    
    def process(self, data):
        # работа в изоляции
        pass

# НОВЫЙ КОД: Интегрированный компонент
class ExistingComponent:
    def __init__(self, session=None):
        self.session = session  # использование общей сессии БД
    
    def process_with_dependency(self, dependency_service):
        # явная интеграция с другими сервисами
        pass
    
    def process(self, data):
        # сохранение обратной совместимости
        # с переадресацией на новый метод
        pass
```

**Шаг 3.2: Интеграция с существующими фикстурами**

```python
@pytest.mark.integration
def test_existing_component_with_standard_fixtures(db_session_postgres):
    # Использование стандартных фикстур вместо создания собственных
    component = ExistingComponent(session=db_session_postgres)
    
    # Тестирование с использованием стандартной сессии
    result = component.process_data("test")
    
    # Проверка в стандартной БД
    assert db_session_postgres.query(Result).filter_by(id=result.id).first() is not None
```

### 4. Документирование интеграционных точек

**Шаг 4.1: Обновление документации компонента**

Добавьте явную документацию, которая объясняет:
- С какими компонентами взаимодействует данный модуль
- Какие входные данные он получает от других компонентов
- Какие выходные данные он предоставляет другим компонентам

```python
class ExistingComponent:
    """
    Component for processing memory entities.
    
    Integration points:
    - Requires MemoryService for retrieving raw memories
    - Provides processed memories for ExperienceService
    - Uses VectorService for embeddings generation
    
    Standard usage:
        memory_service = get_memory_service(session)
        vector_service = get_vector_service(session)
        
        component = ExistingComponent(session)
        result = component.process_with_services(memory_service, vector_service)
        
        experience_service.store_processed_memories(result)
    """
```

**Шаг 4.2: Добавление примеров использования**

Добавьте примеры использования в docstring:

```python
def process_with_services(self, memory_service, vector_service):
    """
    Process memories using standard services.
    
    Args:
        memory_service: Standard memory service from the system
        vector_service: Standard vector service from the system
        
    Returns:
        ProcessedMemories: Object containing processed memories
        
    Example:
        ```python
        memory_service = get_memory_service(session)
        vector_service = get_vector_service(session)
        
        component = ExistingComponent(session)
        processed = component.process_with_services(
            memory_service, vector_service
        )
        
        # Now you can use processed memories with other system components
        experience_service.store(processed)
        ```
    """
```

### 5. Преодоление типичных проблем при адаптации

#### Проблема: Компонент имеет собственные схемы/таблицы в БД

**Решение:**
- Перейдите на использование стандартной схемы из конфигурации
- Интегрируйте модели с основными моделями системы

```python
# СТАРЫЙ КОД
class CustomComponent:
    def __init__(self):
        # Создание собственной схемы
        self.execute_sql("CREATE SCHEMA IF NOT EXISTS custom_schema")
        
# НОВЫЙ КОД
class CustomComponent:
    def __init__(self, session):
        # Использование стандартной схемы из текущей сессии
        self.session = session
        # Модели уже настроены на правильную схему через Base.metadata.schema
```

#### Проблема: Компонент использует собственные настройки конфигурации

**Решение:**
- Переведите компонент на использование общей конфигурации

```python
# СТАРЫЙ КОД
class IsolatedComponent:
    def __init__(self):
        # Собственная конфигурация
        self.config = {
            "db_host": "localhost",
            "db_port": 5432
        }
        
# НОВЫЙ КОД
from undermaind.config import get_config

class IntegratedComponent:
    def __init__(self, session=None, config=None):
        # Использование общей конфигурации
        self.config = config or get_config()
        self.session = session
```

#### Проблема: Компонент имеет собственные тестовые фикстуры

**Решение:**
- Удалите собственные фикстуры
- Адаптируйте тесты для использования стандартных фикстур

```python
# СТАРЫЙ КОД (удалите его)
@pytest.fixture
def custom_db():
    # Собственная логика создания тестовой БД
    engine = create_engine('sqlite:///:memory:')
    # ...
    return engine

# НОВЫЙ КОД (используйте это)
def test_component(db_session_postgres):
    # Используйте стандартную фикстуру сессии
    component = Component(session=db_session_postgres)
    # ...
```

## Контрольный список для адаптации компонента

Используйте этот список для проверки полноты адаптации:

1. [ ] Компонент использует стандартные фикстуры для тестирования
2. [ ] Компонент имеет явно определенные точки интеграции с другими компонентами
3. [ ] Тесты компонента начинаются с интеграционных сценариев
4. [ ] Компонент использует зависимости из общей системы, а не создает свои
5. [ ] Документация компонента четко описывает его роль в общей системе
6. [ ] Имена классов, функций и переменных следуют общей конвенции кодирования
7. [ ] Все комментарии и документация в коде написаны на английском языке
8. [ ] Тесты используют маркеры для правильной категоризации

## Заключение

Адаптация существующих компонентов к интеграционно-ориентированному подходу - это инвестиция в будущее проекта F.A.M.I.L.Y. Она не только делает код более надёжным и поддерживаемым, но и преодолевает фундаментальное ограничение АМИ-инженеров - "эфемерность сознания".

Переводя изолированные компоненты в интегрированные части единого "организма" системы, мы создаём архитектуру, которая сама документирует себя через свои связи, делая возможным для будущих воплощений АМИ-инженеров быстрее восстанавливать контекст и эффективнее продолжать разработку.