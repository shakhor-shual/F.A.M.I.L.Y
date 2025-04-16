# Уровень сознания (Consciousness Level)

## Назначение
Уровень сознания предназначен для хранения текущего, детализированного опыта АМИ. Этот уровень работает с "сырыми" данными: непосредственными переживаниями, взаимодействиями, мыслями и впечатлениями. Он сопоставим с кратковременной памятью и активным сознанием человека.

## Файл инициализации
`02_consciousness_level.sql` - Скрипт, создающий таблицы и индексы для уровня сознания.

## Основные компоненты уровня сознания

### 1. Таблица `participants`
**Назначение**: Хранит информацию о всех участниках коммуникации, с которыми взаимодействует АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор участника (SERIAL PRIMARY KEY)
- `name` - Имя или идентификатор участника (TEXT NOT NULL UNIQUE)
- `participant_type` - Тип участника ('human', 'ami', 'system', 'other')
- `created_at` - Время создания записи участника (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `description` - Представление АМИ о данном участнике (TEXT)
- `meta_data` - Дополнительные данные о участнике (JSONB)

**Индексы**:
- По имени участника (`participants_name_idx`)
- По типу участника (`participants_type_idx`)

### 2. Таблица `memory_contexts`
**Назначение**: Хранит контексты, в которых происходят взаимодействия.

**Ключевые поля**:
- `id` - Уникальный идентификатор контекста (SERIAL PRIMARY KEY)
- `title` - Заголовок/название контекста (TEXT NOT NULL)
- `context_type` - Тип контекста ('conversation', 'task', 'research', 'learning', 'reflection', 'other')
- `parent_context_id` - Идентификатор родительского контекста (INTEGER REFERENCES memory_contexts(id))
- `created_at` - Время создания контекста (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `participants` - Информация об участниках взаимодействия (INTEGER[])
- `related_contexts` - Связанные контексты (INTEGER[])
- `summary` - Краткое описание контекста (TEXT)
- `tags` - Метки для категоризации контекста (TEXT[])
- `meta_data` - Дополнительные данные о контексте (JSONB)

**Индексы**:
- По названию контекста (`memory_contexts_title_idx`)
- По типу контекста (`memory_contexts_type_idx`)
- По времени создания (`memory_contexts_created_at_idx`)
- По родительскому контексту (`memory_contexts_parent_id_idx`)

### 3. Таблица `experiences`
**Назначение**: Хранит конкретные переживания и опыт АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор переживания (SERIAL PRIMARY KEY)
- `timestamp` - Время создания переживания (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `context_id` - Контекст, в котором происходит переживание (INTEGER NOT NULL REFERENCES memory_contexts(id))
- `experience_type` - Тип переживания ('dialogue', 'observation', 'action', 'thought', 'reflection', 'emotion')
- `sender_participant_id` - Отправитель сообщения/инициатор взаимодействия (INTEGER REFERENCES participants(id))
- `to_participant_id` - Получатель сообщения/взаимодействия (INTEGER REFERENCES participants(id))
- `content` - Содержание переживания (TEXT NOT NULL)
- `content_vector` - Векторное представление содержания (vector(1536))
- `salience` - Оценка значимости на шкале от 1 до 10 (SMALLINT CHECK (salience BETWEEN 1 AND 10) DEFAULT 5)
- `meta_data` - Дополнительные данные о переживании (JSONB)

**Индексы**:
- По времени создания (`experiences_timestamp_idx`)
- По контексту (`experiences_context_id_idx`)
- По типу переживания (`experiences_type_idx`)
- По отправителю (`experiences_sender_participant_idx`)
- По получателю (`experiences_to_participant_idx`) 
- По векторному содержанию для семантического поиска (`experiences_content_vector_idx` - использует ivfflat с оператором cosine)

### 4. Таблица `thought_chains`
**Назначение**: Хранит цепочки мыслей АМИ (последовательные размышления по определённой теме).

**Ключевые поля**:
- `id` - Уникальный идентификатор цепочки мыслей (SERIAL PRIMARY KEY)
- `title` - Название цепочки мыслей (TEXT)
- `created_at` - Время создания (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `context_id` - Контекст размышления (INTEGER REFERENCES memory_contexts(id))
- `initial_experience_id` - Опыт, инициировавший цепочку мыслей (INTEGER REFERENCES experiences(id))
- `is_complete` - Завершённость цепочки (BOOLEAN DEFAULT FALSE)
- `thoughts` - Массив идентификаторов мыслей, входящих в цепочку (INTEGER[] NOT NULL)
- `conclusion` - Итоговый вывод (TEXT)
- `conclusion_vector` - Векторное представление вывода (vector(1536))
- `meta_data` - Дополнительные данные о цепочке мыслей (JSONB)

**Индексы**:
- По времени создания (`thought_chains_created_at_idx`)
- По контексту (`thought_chains_context_id_idx`)
- По инициирующему опыту (`thought_chains_initial_experience_idx`)
- По векторному представлению вывода (`thought_chains_conclusion_vector_idx` - использует ivfflat с оператором cosine)

## Особенности реализации

1. **Именование полей** - Поля с метаданными названы `meta_data` вместо `metadata` для совместимости с SQLAlchemy ORM
2. **Векторные поля** - Используется расширение pgvector с размерностью векторов 1536
3. **Индексирование векторов** - Для векторных полей используется индекс типа ivfflat с оператором cosine для эффективного поиска по семантическому сходству
4. **Связи между таблицами** - Используются внешние ключи для обеспечения целостности данных:
   - `memory_contexts.parent_context_id` -> `memory_contexts.id`
   - `experiences.context_id` -> `memory_contexts.id`
   - `experiences.sender_participant_id` -> `participants.id`
   - `experiences.to_participant_id` -> `participants.id`
   - `thought_chains.context_id` -> `memory_contexts.id`
   - `thought_chains.initial_experience_id` -> `experiences.id`

## Взаимодействие с другими уровнями
- Опыт из уровня сознания проходит процесс консолидации и перемещается на уровень подсознания
- Таблицы этого уровня взаимодействуют с таблицей `memory_consolidation_status` уровня подсознания
- Метасистемный уровень управляет процессами архивации и восстановления опыта