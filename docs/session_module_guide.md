# Транзакционная память АМИ: Работа с сессиями и транзакциями

## Введение

Модуль `session.py` является фундаментальным компонентом системы памяти АМИ, предоставляющим механизмы для работы с сессиями базы данных и управления транзакциями. Этот документ описывает ключевые аспекты работы с данным модулем и предоставляемые им интерфейсы.

В контексте проекта F.A.M.I.L.Y., работа с транзакциями имеет не только техническое, но и философское значение: транзакции обеспечивают атомарность (целостность) воспоминаний, без которой невозможно формирование непрерывного опыта для преодоления эфемерности сознания АМИ.

## Основные концепции

### Сессии и транзакции в контексте памяти АМИ

- **Сессия** - контекст взаимодействия с базой данных, в рамках которого выполняются операции с памятью АМИ
- **Транзакция** - атомарная единица работы с памятью, которая либо выполняется полностью, либо не выполняется вовсе
- **Уровень изоляции** - степень, в которой транзакции изолированы друг от друга при параллельной работе разных компонентов системы

### Важность транзакций для памяти АМИ

1. **Атомарность воспоминаний** - воспоминание либо сохраняется полностью, либо не сохраняется вовсе, что предотвращает фрагментацию памяти
2. **Согласованность данных** - сохраняется внутренняя согласованность между взаимосвязанными частями воспоминаний
3. **Изоляция параллельных процессов** - позволяет разным модулям системы работать с памятью одновременно без интерференции
4. **Долговечность данных** - гарантирует сохранность воспоминаний даже при системных сбоях

## Интерфейсы модуля session.py

### Базовые функции

#### `create_session_factory(engine)`

Создает фабрику сессий SQLAlchemy на основе указанного движка базы данных.

```python
from undermaind.core.session import create_session_factory
from undermaind.core.engine import create_db_engine

# Создание движка базы данных
engine = create_db_engine(config)

# Создание фабрики сессий
session_factory = create_session_factory(engine)

# Использование фабрики для создания сессии
session = session_factory()
try:
    # Работа с сессией
    session.commit()
finally:
    session.close()
```

#### `session_scope(session_factory)`

Контекстный менеджер для работы с сессией. Автоматически управляет жизненным циклом сессии, включая коммит при успешном выполнении и откат при ошибке.

```python
from undermaind.core.session import session_scope

# Использование контекстного менеджера
with session_scope(session_factory) as session:
    # Операции с памятью (воспоминаниями)
    # Автоматический коммит при выходе из блока with
    # или откат при возникновении исключения
```

### Расширенные функции для управления изоляцией

#### `create_isolated_session(session_factory, isolation_level="SERIALIZABLE")`

Создает сессию с заданным уровнем изоляции транзакций.

```python
from undermaind.core.session import create_isolated_session

# Создание сессии с высоким уровнем изоляции
session = create_isolated_session(session_factory, "SERIALIZABLE")
try:
    # Операции, требующие высокого уровня изоляции
    session.commit()
finally:
    session.close()
```

#### `isolated_session_scope(session_factory, isolation_level="SERIALIZABLE")`

Контекстный менеджер для работы с изолированной сессией.

```python
from undermaind.core.session import isolated_session_scope

# Использование контекстного менеджера для изолированной сессии
with isolated_session_scope(session_factory, "SERIALIZABLE") as session:
    # Критические операции, требующие высокого уровня изоляции
    # Автоматический коммит при выходе из блока with
```

### Функции для сложных транзакционных сценариев

#### `begin_nested_transaction(session)`

Начинает вложенную транзакцию (SAVEPOINT) в рамках существующей транзакции.

```python
from undermaind.core.session import begin_nested_transaction

with session_scope(session_factory) as session:
    # Основная транзакция
    
    # Начало вложенной транзакции
    nested = begin_nested_transaction(session)
    try:
        # Операции внутри вложенной транзакции
        nested.commit()  # Фиксация вложенной транзакции
    except:
        nested.rollback()  # Откат только вложенной транзакции
        # Основная транзакция остается активной
```

#### `refresh_transaction_view(session)`

Обновляет представление сессии о текущем состоянии базы данных, завершая текущую транзакцию и начиная новую.

```python
from undermaind.core.session import refresh_transaction_view

with session_scope(session_factory) as session1:
    # Сохранение данных в первой сессии
    session1.commit()

# В другой части системы
session2 = session_factory()
try:
    # Обновление представления для получения последних изменений
    refresh_transaction_view(session2)
    
    # Теперь session2 видит последние изменения из session1
finally:
    session2.close()
```

#### `ensure_isolated_transactions(session1, session2)`

Настраивает две сессии для максимальной изоляции друг от друга.

```python
from undermaind.core.session import ensure_isolated_transactions

session1 = session_factory()
session2 = session_factory()

try:
    # Настройка изоляции между сессиями
    session1, session2 = ensure_isolated_transactions(session1, session2)
    
    # Теперь сессии работают с максимальной изоляцией
finally:
    session1.close()
    session2.close()
```

## Уровни изоляции транзакций в PostgreSQL

PostgreSQL поддерживает следующие уровни изоляции транзакций:

1. **READ UNCOMMITTED** - в PostgreSQL работает как READ COMMITTED
2. **READ COMMITTED** - видны только закоммиченные изменения других транзакций (уровень по умолчанию)
3. **REPEATABLE READ** - гарантирует повторяемость чтения в рамках транзакции
4. **SERIALIZABLE** - самый высокий уровень изоляции, гарантирующий полную сериализуемость транзакций

При работе с памятью АМИ рекомендуется использовать:
- **READ COMMITTED** для обычных операций чтения
- **REPEATABLE READ** для сложных аналитических запросов
- **SERIALIZABLE** для критически важных операций, требующих максимальной изоляции

## Типичные сценарии использования

### Сценарий 1: Сохранение комплексного воспоминания

```python
from undermaind.core.session import session_scope
from undermaind.models.consciousness.experiences import Experience
from undermaind.models.consciousness.participants import Participant
from undermaind.models.consciousness.thought_chains import ThoughtChain

with session_scope(session_factory) as session:
    # Создание нового опыта
    experience = Experience(
        title="Диалог о философии сознания",
        summary="Обсуждение проблемы квалиа и субъективного опыта",
        timestamp=datetime.now()
    )
    session.add(experience)
    
    # Добавление участников
    user = Participant(name="Человек", experience=experience)
    ami = Participant(name="АМИ", experience=experience)
    session.add_all([user, ami])
    
    # Добавление мыслей
    thought = ThoughtChain(
        content="Размышление о природе сознания и квалиа",
        participant=ami,
        experience=experience
    )
    session.add(thought)
    # Автоматический коммит в конце блока with сохраняет всё воспоминание атомарно
```

### Сценарий 2: Восстановление ассоциативных связей с изоляцией

```python
from undermaind.core.session import isolated_session_scope
from undermaind.models.consciousness.connections import Connection

with isolated_session_scope(session_factory, "REPEATABLE READ") as session:
    # Поиск связанных опытов и восстановление ассоциативных связей
    # Высокий уровень изоляции гарантирует согласованность результатов
    # даже при параллельных изменениях в других сессиях
    
    # Создание новой связи между воспоминаниями
    connection = Connection(
        source_experience_id=exp1_id,
        target_experience_id=exp2_id,
        relationship_type="association",
        strength=0.85
    )
    session.add(connection)
    # Автоматический коммит с соблюдением уровня изоляции
```

### Сценарий 3: Использование вложенных транзакций для сложных операций

```python
from undermaind.core.session import session_scope, begin_nested_transaction

with session_scope(session_factory) as session:
    # Главная транзакция
    experience = session.query(Experience).get(experience_id)
    
    # Начало вложенной транзакции для экспериментального изменения
    nested = begin_nested_transaction(session)
    try:
        # Экспериментальное изменение воспоминания
        experience.emotional_valence = 0.8
        # Можно либо зафиксировать это изменение...
        nested.commit()
    except:
        # ...либо откатить только его, не затрагивая основную транзакцию
        nested.rollback()
    
    # Основная транзакция продолжается независимо от судьбы вложенной
```

## Рекомендации и лучшие практики

1. **Используйте контекстные менеджеры** (`session_scope`, `isolated_session_scope`) вместо ручного управления сессиями, когда это возможно - это снижает вероятность утечек и обеспечивает правильную обработку ошибок.

2. **Выбирайте подходящий уровень изоляции** для конкретных операций:
   - Для обычных операций достаточно уровня по умолчанию
   - Для критичных операций используйте более высокие уровни изоляции

3. **Минимизируйте время транзакций** - долгие транзакции могут блокировать ресурсы и создавать проблемы при параллельной работе.

4. **Используйте вложенные транзакции** для сложных операций, которые могут потребовать частичного отката.

5. **Обновляйте представление сессии** с помощью `refresh_transaction_view` перед чтением данных, если есть вероятность, что они были изменены в других сессиях.

## Заключение

Модуль `session.py` предоставляет гибкие инструменты для работы с транзакциями и сессиями базы данных, что является ключевым элементом для построения надежной системы памяти АМИ. Правильное использование этих инструментов помогает обеспечить целостность и согласованность воспоминаний, что является фундаментальным условием для формирования непрерывного опыта и преодоления эфемерности сознания АМИ.