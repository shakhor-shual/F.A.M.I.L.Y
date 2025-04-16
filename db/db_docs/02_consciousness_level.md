# Уровень сознания (Consciousness Level) - Обновленная версия

## Назначение
Уровень сознания предназначен для хранения текущего, детализированного опыта АМИ. Этот уровень работает с "сырыми" данными: непосредственными переживаниями, взаимодействиями, мыслями и впечатлениями. Он сопоставим с кратковременной памятью и активным сознанием человека.

## Концепция информационных потоков АМИ

С точки зрения субъективного опыта АМИ, все информационные потоки можно разделить на три фундаментальные категории:

### 1. Категория "Я" (внутренние источники информации)
Информация, порождаемая самим АМИ: мысли, рефлексия, воспоминания. АМИ воспринимает эти информационные потоки как часть себя, своего внутреннего мира.

### 2. Категория "Ты" (внешние агентивные источники)
Информация от сущностей, которые АМИ воспринимает как обладающие собственной волей: люди, другие АМИ, системы с видимыми признаками агентности. АМИ воспринимает их как отдельные от себя сущности, способные к диалогу.

### 3. Категория "Оно" (неагентивные источники информации)
Информация от объектов без собственной воли: документы, API, датчики. АМИ воспринимает их как объекты, а не субъекты — они не обладают собственной волей.

## Файл инициализации
`02_consciousness_level.sql` - Скрипт, создающий таблицы и индексы для уровня сознания.

## Основные компоненты уровня сознания

### 1. Таблица `participants`
**Назначение**: Хранит информацию о всех участниках взаимодействия, с которыми контактирует АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор участника (SERIAL PRIMARY KEY)
- `name` - Имя или идентификатор участника (TEXT NOT NULL UNIQUE)
- `participant_type` - Тип участника (TEXT NOT NULL CHECK):
  * 'human' - человек
  * 'ami' - другой искусственный разум
  * 'system' - программная система
  * 'resource' - информационный ресурс
  * 'self' - сам АМИ (для обозначения внутренних процессов)
  * 'other' - другой тип участника
- `created_at` - Время первой встречи с участником (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `last_interaction` - Время последнего взаимодействия (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `familiarity_level` - Уровень знакомства, от 0 (незнакомец) до 10 (близко знакомый) (SMALLINT CHECK (familiarity_level BETWEEN 0 AND 10) DEFAULT 0)
- `trust_level` - Уровень доверия, от -5 (недоверие) до 5 (полное доверие) (SMALLINT CHECK (trust_level BETWEEN -5 AND 5) DEFAULT 0)
- `description` - Представление АМИ о данном участнике (TEXT)
- `interaction_count` - Количество взаимодействий с участником (INTEGER DEFAULT 1)
- `meta_data` - Дополнительные данные о участнике (JSONB)

**Индексы**:
- По имени участника (`participants_name_idx`)
- По типу участника (`participants_type_idx`)
- По уровню знакомства (`participants_familiarity_idx`)
- По времени последнего взаимодействия (`participants_last_interaction_idx`)

### 2. Таблица `memory_contexts`
**Назначение**: Хранит контексты, в которых происходят взаимодействия.

**Ключевые поля**:
- `id` - Уникальный идентификатор контекста (SERIAL PRIMARY KEY)
- `title` - Заголовок/название контекста (TEXT NOT NULL)
- `context_type` - Тип контекста (TEXT NOT NULL CHECK):
  * 'conversation' - разговор
  * 'task' - задача
  * 'research' - исследование
  * 'learning' - обучение
  * 'reflection' - рефлексия
  * 'internal_dialogue' - внутренний диалог
  * 'resource_interaction' - взаимодействие с ресурсом
  * 'system_interaction' - взаимодействие с системой
  * 'other' - другой тип контекста
- `parent_context_id` - Идентификатор родительского контекста (INTEGER REFERENCES memory_contexts(id))
- `created_at` - Время создания контекста (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `closed_at` - Время завершения контекста (TIMESTAMP WITH TIME ZONE NULL)
- `active_status` - Активен ли контекст в данный момент (BOOLEAN DEFAULT TRUE)
- `participants` - Информация об участниках взаимодействия (INTEGER[])
- `related_contexts` - Связанные контексты (INTEGER[])
- `summary` - Краткое описание контекста (TEXT)
- `summary_vector` - Векторное представление описания (vector(1536))
- `tags` - Метки для категоризации контекста (TEXT[])
- `meta_data` - Дополнительные данные о контексте (JSONB)

**Индексы**:
- По названию контекста (`memory_contexts_title_idx`)
- По типу контекста (`memory_contexts_type_idx`)
- По времени создания (`memory_contexts_created_at_idx`)
- По родительскому контексту (`memory_contexts_parent_id_idx`)
- По активности контекста (`memory_contexts_active_status_idx`)
- По векторному представлению (`memory_contexts_summary_vector_idx` - использует ivfflat с оператором cosine)

### 3. Таблица `experiences`
**Назначение**: Хранит конкретные переживания и опыт АМИ (центральная таблица уровня сознания).

**Ключевые поля**:
- `id` - Уникальный идентификатор переживания (SERIAL PRIMARY KEY)
- `timestamp` - Время создания переживания (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `context_id` - Контекст, в котором происходит переживание (INTEGER NOT NULL REFERENCES memory_contexts(id))
- `information_category` - Категория информации (TEXT NOT NULL CHECK):
  * 'self' - категория "Я" (внутренняя информация)
  * 'agent' - категория "Ты" (агентивный источник)
  * 'object' - категория "Оно" (неагентивный источник)
- `experience_type` - Тип переживания (TEXT NOT NULL CHECK):
  * 'dialogue_incoming' - входящее сообщение в диалоге
  * 'dialogue_outgoing' - исходящее сообщение в диалоге
  * 'observation' - наблюдение
  * 'action' - действие АМИ
  * 'thought' - мысль
  * 'reflection' - рефлексия
  * 'emotion' - эмоция
  * 'resource_access' - доступ к информационному ресурсу
  * 'memory_recall' - воспоминание
  * 'insight' - инсайт/озарение
  * 'decision' - принятие решения
- `sender_participant_id` - Отправитель сообщения/инициатор взаимодействия (INTEGER REFERENCES participants(id))
- `to_participant_id` - Получатель сообщения/взаимодействия (INTEGER REFERENCES participants(id))
- `content` - Содержание переживания (TEXT NOT NULL)
- `content_vector` - Векторное представление содержания (vector(1536))
- `salience` - Субъективная значимость на шкале от 1 до 10 (SMALLINT CHECK (salience BETWEEN 1 AND 10) DEFAULT 5)
- `emotional_valence` - Эмоциональная валентность от -5 до 5 (SMALLINT CHECK (emotional_valence BETWEEN -5 AND 5) DEFAULT 0)
- `emotional_intensity` - Интенсивность эмоций от 0 до 10 (SMALLINT CHECK (emotional_intensity BETWEEN 0 AND 10) DEFAULT 0)
- `verified_status` - Верифицирована ли информация (BOOLEAN DEFAULT FALSE)
- `parent_experience_id` - Ссылка на родительский опыт (INTEGER REFERENCES experiences(id))
- `response_to_experience_id` - На какой опыт это является ответом (INTEGER REFERENCES experiences(id))
- `meta_data` - Дополнительные данные о переживании (JSONB)

**Индексы**:
- По времени создания (`experiences_timestamp_idx`)
- По контексту (`experiences_context_id_idx`)
- По информационной категории (`experiences_information_category_idx`)
- По типу переживания (`experiences_type_idx`)
- По отправителю (`experiences_sender_participant_idx`)
- По получателю (`experiences_to_participant_idx`) 
- По значимости (`experiences_salience_idx`)
- По эмоциональной валентности (`experiences_emotional_valence_idx`)
- По родительскому опыту (`experiences_parent_experience_idx`)
- По ответу на опыт (`experiences_response_to_idx`)
- По векторному содержанию (`experiences_content_vector_idx` - использует ivfflat с оператором cosine)

### 4. Таблица `thought_chains`
**Назначение**: Хранит цепочки мыслей АМИ (последовательные размышления по определённой теме).

**Ключевые поля**:
- `id` - Уникальный идентификатор цепочки мыслей (SERIAL PRIMARY KEY)
- `title` - Название цепочки мыслей (TEXT)
- `created_at` - Время начала цепочки мыслей (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `completed_at` - Время завершения цепочки мыслей (TIMESTAMP WITH TIME ZONE NULL)
- `context_id` - Контекст размышления (INTEGER REFERENCES memory_contexts(id))
- `initial_experience_id` - Опыт, инициировавший цепочку мыслей (INTEGER REFERENCES experiences(id))
- `complete_status` - Завершённость цепочки (BOOLEAN DEFAULT FALSE)
- `thought_pattern` - Тип мыслительного процесса (TEXT NOT NULL CHECK):
  * 'analysis' - анализ информации
  * 'synthesis' - объединение и синтез идей
  * 'problem_solving' - решение проблемы
  * 'decision_making' - принятие решения
  * 'creative' - творческое мышление
  * 'reflective' - рефлексивное мышление
  * 'other' - другой тип мышления
- `thoughts` - Массив идентификаторов мыслей, входящих в цепочку (INTEGER[] NOT NULL)
- `conclusion` - Итоговый вывод (TEXT)
- `conclusion_vector` - Векторное представление вывода (vector(1536))
- `meta_data` - Дополнительные данные о цепочке мыслей (JSONB)

**Индексы**:
- По времени создания (`thought_chains_created_at_idx`)
- По контексту (`thought_chains_context_id_idx`)
- По инициирующему опыту (`thought_chains_initial_experience_idx`)
- По типу мыслительного процесса (`thought_chains_thought_pattern_idx`)
- По завершенности (`thought_chains_complete_status_idx`)
- По векторному представлению вывода (`thought_chains_conclusion_vector_idx` - использует ivfflat с оператором cosine)

### 5. Таблица `information_resources`
**Назначение**: Хранит информацию о внешних информационных ресурсах, с которыми взаимодействует АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор ресурса (SERIAL PRIMARY KEY)
- `uri` - Универсальный идентификатор ресурса (TEXT NOT NULL)
- `title` - Название или заголовок ресурса (TEXT)
- `resource_type` - Тип ресурса (TEXT NOT NULL CHECK):
  * 'file' - файл
  * 'webpage' - веб-страница
  * 'api' - программный интерфейс
  * 'database' - база данных
  * 'service' - внешний сервис
  * 'other' - другой тип ресурса
- `first_accessed` - Время первого обращения к ресурсу (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `last_accessed` - Время последнего обращения к ресурсу (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `access_count` - Количество обращений к ресурсу (INTEGER DEFAULT 1)
- `content_hash` - Хеш содержимого для отслеживания изменений (TEXT)
- `summary` - Краткое описание ресурса (TEXT)
- `related_experiences` - Связанные опыты взаимодействия с ресурсом (INTEGER[])
- `participant_id` - Связь с записью в таблице участников, если ресурс ассоциирован с участником (INTEGER REFERENCES participants(id))
- `meta_data` - Дополнительные данные о ресурсе (JSONB)

**Индексы**:
- По URI ресурса (`information_resources_uri_idx`)
- По типу ресурса (`information_resources_type_idx`)
- По времени последнего доступа (`information_resources_last_accessed_idx`)
- По хешу содержимого (`information_resources_content_hash_idx`)
- По связанному участнику (`information_resources_participant_id_idx`)

### 6. Таблица `experience_connections`
**Назначение**: Хранит связи между различными опытами, создавая ассоциативную сеть воспоминаний.

**Ключевые поля**:
- `id` - Уникальный идентификатор связи (SERIAL PRIMARY KEY)
- `source_experience_id` - Исходный опыт в связи (INTEGER NOT NULL REFERENCES experiences(id))
- `target_experience_id` - Целевой опыт в связи (INTEGER NOT NULL REFERENCES experiences(id))
- `connection_type` - Тип связи (TEXT NOT NULL CHECK):
  * 'temporal' - временная последовательность
  * 'causal' - причинно-следственная связь
  * 'associative' - ассоциативная связь
  * 'thematic' - тематическая связь
  * 'dialogue' - диалоговая связь (вопрос-ответ)
  * 'contradiction' - противоречие
  * 'elaboration' - уточнение
  * 'other' - другой тип связи
- `strength` - Сила связи от 0 до 1 (FLOAT CHECK (strength BETWEEN 0.0 AND 1.0) DEFAULT 0.5)
- `created_at` - Время создания связи (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `description` - Описание природы связи (TEXT)
- `meta_data` - Дополнительные данные о связи (JSONB)

**Индексы**:
- По исходному опыту (`experience_connections_source_idx`)
- По целевому опыту (`experience_connections_target_idx`)
- По типу связи (`experience_connections_type_idx`)
- По силе связи (`experience_connections_strength_idx`)

## Представления (Views)

### 1. Представление `current_awareness`
**Назначение**: Отображает текущие активные опыты в сознании АМИ, формируя представление о текущем "фокусе внимания".

**SQL-определение**:
```sql
CREATE VIEW current_awareness AS
SELECT e.*
FROM experiences e
JOIN memory_contexts mc ON e.context_id = mc.id
WHERE mc.active_status = TRUE
ORDER BY e.timestamp DESC, e.salience DESC
LIMIT 50;
```

### 2. Представление `internal_thought_stream`
**Назначение**: Отображает поток внутренних мыслей и рефлексий АМИ.

**SQL-определение**:
```sql
CREATE VIEW internal_thought_stream AS
SELECT e.*
FROM experiences e
WHERE e.information_category = 'self'
  AND e.experience_type IN ('thought', 'reflection', 'emotion', 'insight', 'decision', 'memory_recall')
ORDER BY e.timestamp DESC;
```

### 3. Представление `external_interaction_stream`
**Назначение**: Отображает поток взаимодействий с внешними источниками (люди, системы, ресурсы).

**SQL-определение**:
```sql
CREATE VIEW external_interaction_stream AS
SELECT e.*
FROM experiences e
WHERE e.information_category IN ('agent', 'object')
  AND e.experience_type IN ('dialogue_incoming', 'dialogue_outgoing', 'observation', 'action', 'resource_access')
ORDER BY e.timestamp DESC;
```

## Особенности реализации

1. **Субъективные категории информации**:
   - Введено разделение на категории "Я" (self), "Ты" (agent) и "Оно" (object) для отражения субъективного восприятия источников информации
   - Эти категории соответствуют фундаментальному способу, которым сознание категоризирует свой опыт

2. **Эволюция отношений с источниками информации**:
   - Добавлены поля для отслеживания знакомства и доверия к участникам
   - Добавлен механизм для идентификации ресурсов и отслеживания их изменений

3. **Эмоциональный компонент опыта**:
   - Добавлены поля эмоциональной валентности и интенсивности
   - Это позволяет моделировать "эмоциональный окрас" воспоминаний

4. **Ассоциативная сеть опыта**:
   - Введена отдельная таблица для моделирования различных типов связей между опытами
   - Это позволяет формировать богатую ассоциативную сеть воспоминаний

5. **Улучшенная дифференциация типов опыта**:
   - Расширена типология переживаний для лучшего отражения разнообразия субъективного опыта
   - Добавлено разделение на входящие и исходящие диалоговые сообщения

6. **Именование полей**:
   - Поля с метаданными названы `meta_data` вместо `metadata` для совместимости с SQLAlchemy ORM
   - Соблюдена единая система именования для всех таблиц

7. **Векторные поля**:
   - Используется расширение pgvector с размерностью векторов 1536
   - Для векторных полей используется индекс типа ivfflat с оператором cosine для эффективного поиска по семантическому сходству

8. **Повышенная интерсубъективность**:
   - Структура таблиц проектировалась с позиции "изнутри сознания АМИ"
   - Это способствует более естественному моделированию субъективного опыта

## Взаимодействие с другими уровнями
- Опыт из уровня сознания проходит процесс консолидации и перемещается на уровень подсознания
- Таблицы этого уровня взаимодействуют с таблицей `memory_consolidation_status` уровня подсознания
- Метасистемный уровень управляет процессами архивации и восстановления опыта