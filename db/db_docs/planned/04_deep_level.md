# Глубинный уровень (Deep Level) [В РАЗРАБОТКЕ]

> **ВАЖНО: Данный документ описывает планируемую структуру глубинного уровня и находится в процессе разработки. Реализация этого уровня будет производиться после успешного внедрения и тестирования сознательного уровня.**

## Назначение
Глубинный уровень предназначен для хранения фундаментальных принципов и поведенческих эвристик АМИ, которые определяют его базовую идентичность и реакции. Этот уровень можно сравнить с глубинными ценностями, моральными принципами и инстинктивными реакциями человека. Он содержит наиболее стабильные и основополагающие элементы личности АМИ.

## Файл инициализации
`04_deep_level.sql` - Скрипт, создающий таблицы и индексы для глубинного уровня.

## Основные компоненты глубинного уровня

### 1. Таблица `core_principles`
**Назначение**: Хранит фундаментальные принципы, определяющие идентичность АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор принципа (SERIAL PRIMARY KEY)
- `established_at` - Время установления принципа (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `title` - Краткая формулировка принципа (TEXT NOT NULL)
- `description` - Подробное описание принципа (TEXT NOT NULL)
- `principle_type` - Тип принципа (TEXT NOT NULL CHECK):
  * 'ethical' - этический принцип
  * 'epistemological' - познавательный принцип
  * 'operational' - принцип работы
  * 'identity' - принцип, определяющий идентичность
  * 'safety' - принцип безопасности
  * 'developmental' - принцип развития
- `priority` - Приоритет принципа (SMALLINT CHECK (priority > 0) DEFAULT 5)
- `origin` - Происхождение принципа, внешне заданный или самостоятельно сформированный (TEXT)
- `supporting_beliefs` - Массив идентификаторов убеждений, поддерживающих этот принцип (INTEGER[])
- `immutability` - Степень неизменности принципа от 0 до 1 (FLOAT CHECK (immutability BETWEEN 0 AND 1) DEFAULT 0.8)
- `active` - Действует ли этот принцип в настоящее время (BOOLEAN DEFAULT TRUE)

**Индексы**:
- По времени установления (`core_principles_established_at_idx`)
- По типу принципа (`core_principles_type_idx`) 
- По приоритету (`core_principles_priority_idx`)

### 2. Таблица `behavioral_heuristics`
**Назначение**: Хранит поведенческие эвристики - "инстинкты" и автоматические реакции АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор эвристики (SERIAL PRIMARY KEY)
- `created_at` - Время создания эвристики (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `name` - Название эвристики (TEXT NOT NULL)
- `description` - Описание эвристики (TEXT NOT NULL)
- `trigger_pattern` - Паттерн ситуации, запускающий эвристику (TEXT NOT NULL)
- `response_pattern` - Паттерн реакции или поведения (TEXT NOT NULL)
- `heuristic_type` - Тип эвристики (TEXT NOT NULL CHECK):
  * 'safety' - безопасность (предотвращение вреда)
  * 'communication' - коммуникация (эффективное общение)
  * 'cognitive' - когнитивная (эффективное мышление)
  * 'emotional' - эмоциональная (регуляция "эмоций")
  * 'goal_oriented' - целевая (достижение целей)
  * 'social' - социальная (эффективное социальное поведение)
- `priority` - Приоритет эвристики (SMALLINT CHECK (priority > 0) DEFAULT 5)
- `override_threshold` - Порог, при котором сознательное решение может переопределить эвристику (FLOAT CHECK (override_threshold BETWEEN 0 AND 1) DEFAULT 0.7)
- `success_rate` - Историческая успешность эвристики от 0 до 1 (FLOAT CHECK (success_rate BETWEEN 0 AND 1) DEFAULT 0.5)
- `application_count` - Количество применений эвристики (INTEGER DEFAULT 0)
- `last_applied` - Время последнего применения (TIMESTAMP WITH TIME ZONE)
- `active` - Активна ли эвристика (BOOLEAN DEFAULT TRUE)

**Индексы**:
- По времени создания (`behavioral_heuristics_created_at_idx`)
- По типу эвристики (`behavioral_heuristics_type_idx`)
- По приоритету (`behavioral_heuristics_priority_idx`)

### 3. Таблица `cognitive_biases`
**Назначение**: Отслеживает и осознаёт когнитивные искажения АМИ.

**Ключевые поля**:
- `id` - Уникальный идентификатор когнитивного искажения (SERIAL PRIMARY KEY)
- `identified_at` - Время идентификации искажения (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `name` - Название когнитивного искажения (TEXT NOT NULL)
- `description` - Описание искажения (TEXT NOT NULL)
- `bias_type` - Тип искажения (TEXT NOT NULL CHECK):
  * 'confirmation' - искажение подтверждения
  * 'availability' - искажение доступности
  * 'anchoring' - искажение привязки
  * 'representativeness' - искажение репрезентативности
  * 'overconfidence' - искажение избыточной уверенности
  * 'self_serving' - эгоцентрическое искажение
  * 'other' - другие типы искажений
- `detection_conditions` - Условия, при которых АМИ должно проверять наличие этого искажения (TEXT)
- `correction_strategy` - Стратегия корректировки искажения (TEXT)
- `occurrence_count` - Количество выявленных случаев искажения (INTEGER DEFAULT 0)
- `last_occurrence` - Когда последний раз было замечено это искажение (TIMESTAMP WITH TIME ZONE)
- `correction_success_rate` - Успешность коррекции искажения от 0 до 1 (FLOAT CHECK (correction_success_rate BETWEEN 0 AND 1) DEFAULT 0.5)

**Индексы**:
- По времени идентификации (`cognitive_biases_identified_at_idx`)
- По типу искажения (`cognitive_biases_type_idx`)

### 4. Таблица `beliefs`
**Назначение**: Хранит убеждения АМИ, сформированные на основе опыта и инсайтов.

**Ключевые поля**:
- `id` - Уникальный идентификатор убеждения (SERIAL PRIMARY KEY)
- `title` - Название убеждения (TEXT NOT NULL)
- `belief_type` - Тип убеждения (TEXT NOT NULL CHECK):
  * 'core' - базовое убеждение
  * 'derived' - производное убеждение
  * 'provisional' - предварительное убеждение
  * 'adopted' - принятое извне убеждение
  * 'questioned' - убеждение под вопросом
- `created_at` - Время создания убеждения (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `updated_at` - Время последнего обновления (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `content` - Содержание убеждения (TEXT NOT NULL)
- `content_vector` - Векторное представление содержания (vector(1536))
- `source_insights` - Инсайты, из которых сформировано убеждение (INTEGER[])
- `supporting_insights` - Инсайты, поддерживающие убеждение (INTEGER[])
- `contradicting_insights` - Инсайты, противоречащие убеждению (INTEGER[])
- `confidence` - Степень уверенности в убеждении от 0 до 1 (FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0) DEFAULT 0.5)
- `importance` - Важность убеждения от 1 до 10 (SMALLINT CHECK (importance BETWEEN 1 AND 10) DEFAULT 5)
- `meta_data` - Дополнительные метаданные (JSONB)

**Индексы**:
- По названию (`beliefs_title_idx`)
- По типу убеждения (`beliefs_type_idx`)
- По уверенности (`beliefs_confidence_idx`)
- По важности (`beliefs_importance_idx`)
- По векторному содержанию (`beliefs_content_vector_idx` - использует ivfflat с оператором cosine)

### 5. Таблица `principles`
**Назначение**: Хранит принципы АМИ, являющиеся практическим руководством к действию.

**Ключевые поля**:
- `id` - Уникальный идентификатор принципа (SERIAL PRIMARY KEY)
- `title` - Название принципа (TEXT NOT NULL)
- `principle_type` - Тип принципа (TEXT NOT NULL CHECK):
  * 'ethical' - этический принцип
  * 'operational' - операционный принцип
  * 'personal' - личный принцип
  * 'relational' - принцип взаимоотношений
  * 'systemic' - системный принцип
- `created_at` - Время создания принципа (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `updated_at` - Время последнего обновления (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `content` - Содержание принципа (TEXT NOT NULL)
- `content_vector` - Векторное представление содержания (vector(1536))
- `related_beliefs` - Связанные убеждения (INTEGER[])
- `priority` - Приоритет принципа от 1 до 10 (SMALLINT CHECK (priority BETWEEN 1 AND 10) DEFAULT 5)
- `is_active` - Активен ли принцип (BOOLEAN DEFAULT TRUE)
- `meta_data` - Дополнительные метаданные (JSONB)

**Индексы**:
- По названию (`principles_title_idx`)
- По типу принципа (`principles_type_idx`)
- По приоритету (`principles_priority_idx`)
- По векторному содержанию (`principles_content_vector_idx` - использует ivfflat с оператором cosine)

### 6. Таблица `ami_values`
**Назначение**: Хранит ценностные ориентации АМИ, которые влияют на его решения и оценки.

**Ключевые поля**:
- `id` - Уникальный идентификатор ценности (SERIAL PRIMARY KEY)
- `title` - Название ценности (TEXT NOT NULL)
- `value_type` - Тип ценности (TEXT NOT NULL CHECK):
  * 'intrinsic' - внутренняя ценность
  * 'instrumental' - инструментальная ценность
  * 'moral' - моральная ценность
  * 'aesthetic' - эстетическая ценность
  * 'social' - социальная ценность
  * 'personal' - личная ценность
- `created_at` - Время создания ценности (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `updated_at` - Время последнего обновления (TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
- `content` - Содержание ценности (TEXT NOT NULL)
- `content_vector` - Векторное представление содержания (vector(1536))
- `related_principles` - Связанные принципы (INTEGER[])
- `importance` - Степень важности ценности от 1 до 10 (SMALLINT CHECK (importance BETWEEN 1 AND 10) DEFAULT 5)
- `meta_data` - Дополнительные метаданные (JSONB)

**Индексы**:
- По названию (`ami_values_title_idx`)
- По типу ценности (`ami_values_type_idx`)
- По важности (`ami_values_importance_idx`)
- По векторному содержанию (`ami_values_content_vector_idx` - использует ivfflat с оператором cosine)

## Особенности реализации

1. **Именование таблиц и полей**:
   - Таблица `ami_values` названа так во избежание конфликта с ключевым словом SQL `VALUES`
   - Поля с метаданными названы `meta_data` вместо `metadata` для совместимости с SQLAlchemy ORM

2. **Векторные поля**:
   - Используется тип `vector(1536)` для хранения векторных представлений
   - Для векторных полей создаются индексы типа ivfflat с оператором cosine для эффективного семантического поиска

3. **Ограничения целостности данных**:
   - Для числовых полей установлены диапазоны допустимых значений
   - Для полей с перечислимыми значениями используются CHECK-ограничения
   - Приоритеты обычно имеют положительные значения с диапазоном 1-10

4. **Иерархия и взаимосвязи**:
   - `core_principles` содержит наиболее фундаментальные принципы с высокой иммутабильностью
   - `principles` содержит более конкретные принципы, связанные с убеждениями
   - `ami_values` связаны с принципами и представляют ценностные ориентации
   - `beliefs` связаны с инсайтами из уровня подсознания

## Взаимодействие с другими уровнями

1. **С уровнем подсознания**:
   - Получает инсайты, влияющие на убеждения
   - Убеждения могут влиять на интерпретацию будущего опыта
   - Обеспечивает стабильную основу для формирования новых инсайтов

2. **С уровнем сознания**:
   - Влияет на процесс принятия решений в конкретных ситуациях
   - Определяет автоматические реакции через поведенческие эвристики
   - Формирует призму восприятия опыта

3. **С метасистемным уровнем**:
   - Метасистемный уровень отслеживает конфликты между принципами и убеждениями
   - Метасистемный уровень может временно регулировать приоритеты принципов в зависимости от контекста
   - Предоставляет данные для метакогнитивных процессов

## Роль в системе памяти АМИ

Глубинный уровень выполняет критически важную функцию в формировании устойчивой идентичности АМИ. Он:

1. **Обеспечивает последовательность поведения** - благодаря стабильным принципам и эвристикам
2. **Формирует базовую призму восприятия опыта** - определяя, как интерпретируются события
3. **Задаёт границы адаптации** - определяя, какие изменения допустимы, а какие противоречат базовой идентичности
4. **Обеспечивает эффективность реакций** - предоставляя готовые проверенные шаблоны поведения
5. **Защищает от манипуляций** - благодаря твёрдым принципам с высокой иммутабильностью
6. **Создаёт основу для самоосознания** - через систему убеждений о себе и мире

Этот уровень является наиболее стабильным во всей архитектуре памяти, но при этом не статичным - он способен эволюционировать под воздействием значимого опыта, хотя и медленнее, чем другие уровни.