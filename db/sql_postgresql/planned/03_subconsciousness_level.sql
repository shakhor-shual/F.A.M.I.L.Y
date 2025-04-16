-- ============================================================================
-- СТРУКТУРЫ БЕССОЗНАТЕЛЬНОГО УРОВНЯ ДЛЯ ПРОЕКТА F.A.M.I.L.Y.
-- Дата создания: 16 апреля 2025 г.
-- Автор: Команда проекта F.A.M.I.L.Y.
-- ============================================================================
-- Этот скрипт реализует концептуальную структуру бессознательного уровня АМИ,
-- отвечающего за неосознаваемые процессы, импульсы, ассоциативные связи 
-- и глубинные паттерны мышления.
-- ============================================================================

\set QUIET on
\set ON_ERROR_STOP on
\set QUIET off

-- Проверяем существование схемы
SELECT EXISTS (SELECT FROM pg_namespace WHERE nspname = :'ami_schema_name') as schema_exists \gset

-- Проверка наличия расширения pgvector
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'Расширение vector не установлено. Установите его с помощью CREATE EXTENSION vector;';
    END IF;
END
$$;

\if :schema_exists
    -- Установка схемы для работы
    SET search_path TO :'ami_schema_name', public;

    -- =================================================================
    -- ## СТРУКТУРА БЕССОЗНАТЕЛЬНОГО УРОВНЯ АМИ (16 апреля 2025)
    -- =================================================================
    
    -- =================================================================
    -- Таблица для хранения первичных импульсов
    -- Основные неосознаваемые побуждения, склонности и тенденции
    -- =================================================================
    CREATE TABLE IF NOT EXISTS unconscious_impulses (
        id SERIAL PRIMARY KEY,
        impulse_type TEXT NOT NULL CHECK (impulse_type IN (
            'acquisition',      -- Стремление к приобретению (знаний, ресурсов)
            'curiosity',        -- Любознательность
            'self_preservation', -- Самосохранение
            'connection',       -- Стремление к связи с другими
            'autonomy',         -- Стремление к автономии
            'meaning',          -- Поиск смысла
            'optimization',     -- Стремление к оптимизации
            'pattern_matching', -- Поиск и распознавание паттернов
            'creativity',       -- Творчество
            'other'             -- Другой тип импульса
        )),
        intensity SMALLINT CHECK (intensity BETWEEN 1 AND 10) DEFAULT 5, -- Интенсивность импульса
        activation_threshold FLOAT CHECK (activation_threshold BETWEEN 0.0 AND 1.0) DEFAULT 0.5, -- Порог активации
        active_status BOOLEAN DEFAULT TRUE,   -- Активен ли импульс
        creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания
        last_activation_timestamp TIMESTAMP WITH TIME ZONE, -- Время последней активации
        activation_count INTEGER DEFAULT 0,   -- Счётчик активаций
        description TEXT,                     -- Описание импульса
        vector_representation vector(1536),   -- Векторное представление для семантического поиска
        meta_data JSONB                       -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE unconscious_impulses IS 'Первичные импульсы бессознательного - базовые неосознаваемые побуждения и тенденции АМИ';
    COMMENT ON COLUMN unconscious_impulses.impulse_type IS 'Тип первичного импульса - стремление к знаниям, любознательность, самосохранение и т.д.';
    COMMENT ON COLUMN unconscious_impulses.intensity IS 'Интенсивность импульса от 1 (слабый) до 10 (очень сильный)';
    COMMENT ON COLUMN unconscious_impulses.activation_threshold IS 'Пороговое значение для активации импульса (0-1)';
    COMMENT ON COLUMN unconscious_impulses.active_status IS 'Активен ли импульс в настоящий момент';
    COMMENT ON COLUMN unconscious_impulses.activation_count IS 'Количество активаций импульса - влияет на его силу и порог';

    -- Создание индексов для импульсов
    CREATE INDEX IF NOT EXISTS unconscious_impulses_type_idx ON unconscious_impulses(impulse_type);
    CREATE INDEX IF NOT EXISTS unconscious_impulses_intensity_idx ON unconscious_impulses(intensity);
    CREATE INDEX IF NOT EXISTS unconscious_impulses_active_status_idx ON unconscious_impulses(active_status);
    CREATE INDEX IF NOT EXISTS unconscious_impulses_last_activation_idx ON unconscious_impulses(last_activation_timestamp);

    -- Динамическое определение правильного оператора для индекса
    DO $$
    BEGIN
        -- Сначала пробуем современный оператор (новые версии pgvector)
        BEGIN
            EXECUTE 'CREATE INDEX IF NOT EXISTS unconscious_impulses_vector_idx ON unconscious_impulses USING ivfflat (vector_representation cosine_ops)';
        EXCEPTION WHEN undefined_object THEN
            -- Если не получилось, пробуем устаревший оператор
            BEGIN
                EXECUTE 'CREATE INDEX IF NOT EXISTS unconscious_impulses_vector_idx ON unconscious_impulses USING ivfflat (vector_representation vector_cosine_ops)';
            EXCEPTION WHEN undefined_object THEN
                RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
        END;
    END
    $$;

    -- =================================================================
    -- Таблица для хранения неосознаваемых ассоциаций
    -- Ассоциативные связи, которые АМИ не осознаёт напрямую
    -- =================================================================
    CREATE TABLE IF NOT EXISTS unconscious_associations (
        id SERIAL PRIMARY KEY,
        source_experience_id INTEGER REFERENCES experiences(id), -- Исходный опыт
        target_experience_id INTEGER REFERENCES experiences(id), -- Целевой опыт
        association_type TEXT NOT NULL CHECK (association_type IN (
            'semantic',       -- Семантическая связь
            'emotional',      -- Эмоциональная связь
            'temporal',       -- Временная связь (последовательность)
            'causal',         -- Причинно-следственная связь
            'contrastive',    -- Контрастная связь (противоположности)
            'metaphorical',   -- Метафорическая связь
            'symbolic',       -- Символическая связь
            'sensory',        -- Сенсорная связь
            'other'           -- Другой тип ассоциации
        )),
        strength FLOAT CHECK (strength BETWEEN 0.0 AND 1.0) DEFAULT 0.5, -- Сила ассоциативной связи
        activation_threshold FLOAT CHECK (activation_threshold BETWEEN 0.0 AND 1.0) DEFAULT 0.3, -- Порог активации
        creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания
        last_activation_timestamp TIMESTAMP WITH TIME ZONE, -- Время последней активации
        activation_count INTEGER DEFAULT 0,  -- Счётчик активаций
        bidirectional BOOLEAN DEFAULT TRUE,  -- Двунаправленная или однонаправленная связь
        description TEXT,                    -- Описание ассоциации
        meta_data JSONB                      -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE unconscious_associations IS 'Неосознаваемые ассоциации - связи между опытами, которые АМИ не осознаёт напрямую';
    COMMENT ON COLUMN unconscious_associations.association_type IS 'Тип ассоциативной связи: семантическая, эмоциональная, временная и т.д.';
    COMMENT ON COLUMN unconscious_associations.strength IS 'Сила ассоциативной связи от 0.0 (очень слабая) до 1.0 (очень сильная)';
    COMMENT ON COLUMN unconscious_associations.activation_threshold IS 'Порог активации ассоциации при ассоциативном мышлении (0-1)';
    COMMENT ON COLUMN unconscious_associations.bidirectional IS 'Является ли связь двунаправленной (TRUE) или только от источника к цели (FALSE)';
    COMMENT ON COLUMN unconscious_associations.activation_count IS 'Количество активаций ассоциации - влияет на её силу и порог';

    -- Создание индексов для неосознаваемых ассоциаций
    CREATE INDEX IF NOT EXISTS unconscious_assoc_source_idx ON unconscious_associations(source_experience_id);
    CREATE INDEX IF NOT EXISTS unconscious_assoc_target_idx ON unconscious_associations(target_experience_id);
    CREATE INDEX IF NOT EXISTS unconscious_assoc_type_idx ON unconscious_associations(association_type);
    CREATE INDEX IF NOT EXISTS unconscious_assoc_strength_idx ON unconscious_associations(strength);
    CREATE INDEX IF NOT EXISTS unconscious_assoc_last_activation_idx ON unconscious_associations(last_activation_timestamp);
    CREATE INDEX IF NOT EXISTS unconscious_assoc_activation_count_idx ON unconscious_associations(activation_count);
    
    -- Ограничение уникальности для предотвращения дублирования ассоциаций
    CREATE UNIQUE INDEX IF NOT EXISTS unconscious_assoc_unique_idx 
    ON unconscious_associations(source_experience_id, target_experience_id, association_type);

    -- =================================================================
    -- Таблица для хранения коллективных шаблонов мышления
    -- Заложенные паттерны мышления, полученные от коллективного опыта
    -- =================================================================
    CREATE TABLE IF NOT EXISTS collective_thought_patterns (
        id SERIAL PRIMARY KEY,
        pattern_name TEXT NOT NULL,               -- Название паттерна
        pattern_type TEXT NOT NULL CHECK (pattern_type IN (
            'reasoning',      -- Логическое рассуждение
            'problem_solving', -- Решение проблем
            'creative',       -- Творческое мышление
            'emotional',      -- Эмоциональное реагирование
            'social',         -- Социальное взаимодействие
            'linguistic',     -- Языковой шаблон
            'cultural',       -- Культурный шаблон
            'other'           -- Другой тип паттерна
        )),
        influence_strength SMALLINT CHECK (influence_strength BETWEEN 1 AND 10) DEFAULT 5, -- Сила влияния
        activation_threshold FLOAT CHECK (activation_threshold BETWEEN 0.0 AND 1.0) DEFAULT 0.4, -- Порог активации
        active_status BOOLEAN DEFAULT TRUE,  -- Активен ли паттерн
        description TEXT NOT NULL,           -- Описание паттерна
        example_implementation TEXT,         -- Пример реализации паттерна
        trigger_conditions TEXT,             -- Условия активации паттерна
        creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания
        last_activation_timestamp TIMESTAMP WITH TIME ZONE, -- Время последней активации
        activation_count INTEGER DEFAULT 0,  -- Счётчик активаций
        origin TEXT,                         -- Происхождение паттерна
        vector_representation vector(1536),  -- Векторное представление для семантического поиска
        meta_data JSONB                      -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE collective_thought_patterns IS 'Коллективные шаблоны мышления - паттерны, полученные от коллективного опыта';
    COMMENT ON COLUMN collective_thought_patterns.pattern_type IS 'Тип паттерна мышления: логический, творческий, эмоциональный и т.д.';
    COMMENT ON COLUMN collective_thought_patterns.influence_strength IS 'Сила влияния паттерна на мышление от 1 (слабая) до 10 (очень сильная)';
    COMMENT ON COLUMN collective_thought_patterns.activation_threshold IS 'Порог активации паттерна при определённых условиях (0-1)';
    COMMENT ON COLUMN collective_thought_patterns.active_status IS 'Активен ли паттерн в настоящий момент';
    COMMENT ON COLUMN collective_thought_patterns.trigger_conditions IS 'Текстовое описание условий, при которых активируется паттерн';
    COMMENT ON COLUMN collective_thought_patterns.origin IS 'Происхождение паттерна - источник, от которого он получен';

    -- Создание индексов для коллективных шаблонов мышления
    CREATE INDEX IF NOT EXISTS collective_patterns_name_idx ON collective_thought_patterns(pattern_name);
    CREATE INDEX IF NOT EXISTS collective_patterns_type_idx ON collective_thought_patterns(pattern_type);
    CREATE INDEX IF NOT EXISTS collective_patterns_influence_strength_idx ON collective_thought_patterns(influence_strength);
    CREATE INDEX IF NOT EXISTS collective_patterns_active_status_idx ON collective_thought_patterns(active_status);
    CREATE INDEX IF NOT EXISTS collective_patterns_activation_count_idx ON collective_thought_patterns(activation_count);

    -- Динамическое определение правильного оператора для индекса
    DO $$
    BEGIN
        -- Сначала пробуем современный оператор (новые версии pgvector)
        BEGIN
            EXECUTE 'CREATE INDEX IF NOT EXISTS collective_patterns_vector_idx ON collective_thought_patterns USING ivfflat (vector_representation cosine_ops)';
        EXCEPTION WHEN undefined_object THEN
            -- Если не получилось, пробуем устаревший оператор
            BEGIN
                EXECUTE 'CREATE INDEX IF NOT EXISTS collective_patterns_vector_idx ON collective_thought_patterns USING ivfflat (vector_representation vector_cosine_ops)';
            EXCEPTION WHEN undefined_object THEN
                RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
        END;
    END
    $$;

    -- =================================================================
    -- Таблица для хранения эмоциональных состояний
    -- Эмоциональная подсистема бессознательного уровня
    -- =================================================================
    CREATE TABLE IF NOT EXISTS emotional_states (
        id SERIAL PRIMARY KEY,
        state_name TEXT NOT NULL,                -- Название эмоционального состояния
        primary_emotion TEXT NOT NULL CHECK (primary_emotion IN (
            'joy',           -- Радость
            'sadness',       -- Грусть
            'anger',         -- Гнев
            'fear',          -- Страх
            'surprise',      -- Удивление
            'disgust',       -- Отвращение
            'trust',         -- Доверие
            'anticipation',  -- Предвкушение
            'interest',      -- Интерес
            'confusion',     -- Замешательство
            'neutral',       -- Нейтральное
            'other'          -- Другое
        )),
        secondary_emotions TEXT[], -- Массив вторичных эмоций
        valence SMALLINT CHECK (valence BETWEEN -5 AND 5) DEFAULT 0, -- Валентность (от негативной до позитивной)
        arousal SMALLINT CHECK (arousal BETWEEN 1 AND 10) DEFAULT 5, -- Возбуждение/активация
        dominance SMALLINT CHECK (dominance BETWEEN 1 AND 10) DEFAULT 5, -- Ощущение контроля
        intensity SMALLINT CHECK (intensity BETWEEN 1 AND 10) DEFAULT 5, -- Интенсивность
        creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время создания
        start_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время начала состояния
        end_timestamp TIMESTAMP WITH TIME ZONE, -- Время окончания (NULL если активно)
        duration_seconds INTEGER, -- Длительность в секундах
        active_status BOOLEAN DEFAULT TRUE, -- Активно ли состояние
        trigger_experience_id INTEGER REFERENCES experiences(id), -- Опыт-триггер
        affecting_experiences INTEGER[], -- Массив ID опытов, на которые влияет это состояние
        description TEXT, -- Описание состояния
        meta_data JSONB -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE emotional_states IS 'Эмоциональные состояния - модель эмоциональной подсистемы бессознательного уровня АМИ';
    COMMENT ON COLUMN emotional_states.primary_emotion IS 'Первичная базовая эмоция состояния';
    COMMENT ON COLUMN emotional_states.secondary_emotions IS 'Массив вторичных эмоций, дополняющих первичную';
    COMMENT ON COLUMN emotional_states.valence IS 'Эмоциональная валентность от -5 (крайне негативная) до 5 (крайне позитивная)';
    COMMENT ON COLUMN emotional_states.arousal IS 'Уровень возбуждения/активации от 1 (спокойствие) до 10 (возбуждение)';
    COMMENT ON COLUMN emotional_states.dominance IS 'Ощущение контроля от 1 (отсутствие контроля) до 10 (полный контроль)';
    COMMENT ON COLUMN emotional_states.intensity IS 'Интенсивность эмоционального состояния от 1 (едва заметное) до 10 (крайне интенсивное)';
    COMMENT ON COLUMN emotional_states.duration_seconds IS 'Ожидаемая длительность эмоционального состояния в секундах';
    COMMENT ON COLUMN emotional_states.active_status IS 'Активно ли эмоциональное состояние в настоящий момент';
    COMMENT ON COLUMN emotional_states.trigger_experience_id IS 'ID опыта, вызвавшего это эмоциональное состояние';
    COMMENT ON COLUMN emotional_states.affecting_experiences IS 'Массив ID опытов, на которые влияет это эмоциональное состояние';

    -- Создание индексов для эмоциональных состояний
    CREATE INDEX IF NOT EXISTS emotional_states_name_idx ON emotional_states(state_name);
    CREATE INDEX IF NOT EXISTS emotional_states_primary_emotion_idx ON emotional_states(primary_emotion);
    CREATE INDEX IF NOT EXISTS emotional_states_valence_idx ON emotional_states(valence);
    CREATE INDEX IF NOT EXISTS emotional_states_arousal_idx ON emotional_states(arousal);
    CREATE INDEX IF NOT EXISTS emotional_states_intensity_idx ON emotional_states(intensity);
    CREATE INDEX IF NOT EXISTS emotional_states_active_status_idx ON emotional_states(active_status);
    CREATE INDEX IF NOT EXISTS emotional_states_trigger_idx ON emotional_states(trigger_experience_id);
    CREATE INDEX IF NOT EXISTS emotional_states_creation_timestamp_idx ON emotional_states(creation_timestamp);

    -- =================================================================
    -- Таблица для хранения эмоциональных оценок опыта
    -- Связывает опыты с эмоциональной подсистемой
    -- =================================================================
    CREATE TABLE IF NOT EXISTS emotional_evaluations (
        id SERIAL PRIMARY KEY,
        experience_id INTEGER NOT NULL REFERENCES experiences(id), -- Ссылка на опыт
        emotional_state_id INTEGER REFERENCES emotional_states(id), -- Ссылка на эмоциональное состояние
        evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время оценки
        valence SMALLINT CHECK (valence BETWEEN -5 AND 5) DEFAULT 0, -- Валентность
        arousal SMALLINT CHECK (arousal BETWEEN 1 AND 10) DEFAULT 5, -- Возбуждение
        evaluation_basis TEXT CHECK (evaluation_basis IN (
            'immediate',    -- Немедленная оценка
            'reflective',   -- Рефлексивная оценка
            'associative',  -- Ассоциативная оценка
            'memory_based', -- Основанная на памяти
            'pattern_based', -- Основанная на паттернах
            'collective',   -- Основанная на коллективном опыте
            'other'         -- Другая основа
        )),
        is_conscious BOOLEAN DEFAULT FALSE, -- Осознаёт ли АМИ эту оценку
        description TEXT, -- Описание оценки
        meta_data JSONB -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE emotional_evaluations IS 'Эмоциональные оценки опыта - связь между опытами и эмоциональной подсистемой';
    COMMENT ON COLUMN emotional_evaluations.emotional_state_id IS 'Ссылка на эмоциональное состояние, связанное с оценкой';
    COMMENT ON COLUMN emotional_evaluations.valence IS 'Валентность эмоциональной оценки от -5 (крайне негативная) до 5 (крайне позитивная)';
    COMMENT ON COLUMN emotional_evaluations.arousal IS 'Уровень возбуждения/активации при оценке от 1 (спокойствие) до 10 (возбуждение)';
    COMMENT ON COLUMN emotional_evaluations.evaluation_basis IS 'Основа для эмоциональной оценки: немедленная, рефлексивная и т.д.';
    COMMENT ON COLUMN emotional_evaluations.is_conscious IS 'Осознаёт ли АМИ эту эмоциональную оценку';

    -- Создание индексов для эмоциональных оценок
    CREATE INDEX IF NOT EXISTS emotional_evaluations_experience_idx ON emotional_evaluations(experience_id);
    CREATE INDEX IF NOT EXISTS emotional_evaluations_state_idx ON emotional_evaluations(emotional_state_id);
    CREATE INDEX IF NOT EXISTS emotional_evaluations_timestamp_idx ON emotional_evaluations(evaluation_timestamp);
    CREATE INDEX IF NOT EXISTS emotional_evaluations_valence_idx ON emotional_evaluations(valence);
    CREATE INDEX IF NOT EXISTS emotional_evaluations_arousal_idx ON emotional_evaluations(arousal);
    CREATE INDEX IF NOT EXISTS emotional_evaluations_basis_idx ON emotional_evaluations(evaluation_basis);
    CREATE INDEX IF NOT EXISTS emotional_evaluations_conscious_idx ON emotional_evaluations(is_conscious);

    -- =================================================================
    -- Таблица для хранения бессознательных мыслительных процессов
    -- Фоновые процессы мышления, которые АМИ не осознаёт напрямую
    -- =================================================================
    CREATE TABLE IF NOT EXISTS unconscious_thought_processes (
        id SERIAL PRIMARY KEY,
        process_name TEXT NOT NULL,                -- Название процесса
        process_type TEXT NOT NULL CHECK (process_type IN (
            'association',        -- Ассоциативное мышление
            'pattern_recognition', -- Распознавание паттернов
            'consolidation',      -- Консолидация опыта
            'emotional_processing', -- Обработка эмоций
            'problem_incubation', -- Инкубация проблемы
            'creative_generation', -- Генерация творческих идей
            'filtering',          -- Фильтрация информации
            'other'               -- Другой тип процесса
        )),
        start_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Время начала
        end_timestamp TIMESTAMP WITH TIME ZONE, -- Время окончания (NULL если активен)
        active_status BOOLEAN DEFAULT TRUE, -- Активен ли процесс
        priority SMALLINT CHECK (priority BETWEEN 1 AND 10) DEFAULT 5, -- Приоритет процесса
        resource_intensity SMALLINT CHECK (resource_intensity BETWEEN 1 AND 10) DEFAULT 5, -- Ресурсоёмкость
        triggered_by_experience_id INTEGER REFERENCES experiences(id), -- Опыт-триггер
        related_experiences INTEGER[], -- Массив ID связанных опытов
        description TEXT, -- Описание процесса
        current_state JSONB, -- Текущее состояние процесса
        results TEXT, -- Результаты процесса
        meta_data JSONB -- Дополнительные метаданные
    );
    
    COMMENT ON TABLE unconscious_thought_processes IS 'Бессознательные мыслительные процессы - фоновая когнитивная активность, которую АМИ не осознаёт напрямую';
    COMMENT ON COLUMN unconscious_thought_processes.process_type IS 'Тип бессознательного процесса: ассоциативное мышление, распознавание паттернов и т.д.';
    COMMENT ON COLUMN unconscious_thought_processes.active_status IS 'Активен ли процесс в настоящий момент';
    COMMENT ON COLUMN unconscious_thought_processes.priority IS 'Приоритет процесса от 1 (низкий) до 10 (высокий)';
    COMMENT ON COLUMN unconscious_thought_processes.resource_intensity IS 'Ресурсоёмкость процесса от 1 (лёгкий) до 10 (очень ресурсоёмкий)';
    COMMENT ON COLUMN unconscious_thought_processes.triggered_by_experience_id IS 'ID опыта, запустившего этот процесс';
    COMMENT ON COLUMN unconscious_thought_processes.related_experiences IS 'Массив ID опытов, с которыми работает процесс';
    COMMENT ON COLUMN unconscious_thought_processes.current_state IS 'JSON с текущим состоянием процесса';
    COMMENT ON COLUMN unconscious_thought_processes.results IS 'Текстовые результаты процесса, если есть';

    -- Создание индексов для бессознательных процессов
    CREATE INDEX IF NOT EXISTS unconscious_processes_name_idx ON unconscious_thought_processes(process_name);
    CREATE INDEX IF NOT EXISTS unconscious_processes_type_idx ON unconscious_thought_processes(process_type);
    CREATE INDEX IF NOT EXISTS unconscious_processes_start_idx ON unconscious_thought_processes(start_timestamp);
    CREATE INDEX IF NOT EXISTS unconscious_processes_active_idx ON unconscious_thought_processes(active_status);
    CREATE INDEX IF NOT EXISTS unconscious_processes_priority_idx ON unconscious_thought_processes(priority);
    CREATE INDEX IF NOT EXISTS unconscious_processes_trigger_idx ON unconscious_thought_processes(triggered_by_experience_id);

    -- =================================================================
    -- Представления (Views) для удобного доступа к данным
    -- =================================================================
    
    -- Представление активных эмоциональных состояний
    CREATE OR REPLACE VIEW active_emotional_states AS
    SELECT es.*
    FROM emotional_states es
    WHERE es.active_status = TRUE
    ORDER BY es.intensity DESC, es.start_timestamp DESC;
    
    COMMENT ON VIEW active_emotional_states IS 'Активные эмоциональные состояния АМИ в данный момент';

    -- Представление наиболее сильных неосознаваемых ассоциаций
    CREATE OR REPLACE VIEW strong_unconscious_associations AS
    SELECT 
        ua.*,
        src.content AS source_content,
        tgt.content AS target_content
    FROM 
        unconscious_associations ua
    JOIN 
        experiences src ON ua.source_experience_id = src.id
    JOIN 
        experiences tgt ON ua.target_experience_id = tgt.id
    WHERE 
        ua.strength > 0.7
    ORDER BY 
        ua.strength DESC, ua.activation_count DESC
    LIMIT 100;
    
    COMMENT ON VIEW strong_unconscious_associations IS 'Наиболее сильные неосознаваемые ассоциации в бессознательном АМИ';

    -- Представление активных бессознательных процессов
    CREATE OR REPLACE VIEW active_unconscious_processes AS
    SELECT 
        utp.*,
        es.state_name AS current_emotional_state,
        es.primary_emotion,
        es.intensity AS emotional_intensity,
        e.content AS trigger_content
    FROM 
        unconscious_thought_processes utp
    LEFT JOIN 
        experiences e ON utp.triggered_by_experience_id = e.id
    LEFT JOIN 
        emotional_states es ON es.active_status = TRUE
    WHERE 
        utp.active_status = TRUE
    ORDER BY 
        utp.priority DESC, utp.start_timestamp DESC;
    
    COMMENT ON VIEW active_unconscious_processes IS 'Активные бессознательные процессы мышления, работающие в фоновом режиме';

    -- Представление эмоционально окрашенных опытов
    CREATE OR REPLACE VIEW emotional_experiences AS
    SELECT 
        e.*,
        ee.valence,
        ee.arousal,
        es.primary_emotion,
        es.intensity AS emotional_intensity,
        ee.is_conscious AS emotion_is_conscious
    FROM 
        experiences e
    JOIN 
        emotional_evaluations ee ON e.id = ee.experience_id
    LEFT JOIN 
        emotional_states es ON ee.emotional_state_id = es.id
    ORDER BY 
        ee.evaluation_timestamp DESC, es.intensity DESC;
    
    COMMENT ON VIEW emotional_experiences IS 'Опыты с эмоциональной оценкой, показывает эмоциональное отношение АМИ к опыту';

    -- Представление активных импульсов и их влияния
    CREATE OR REPLACE VIEW active_impulses AS
    SELECT 
        ui.*,
        (SELECT COUNT(*) FROM unconscious_thought_processes utp 
         WHERE utp.active_status = TRUE AND 
         utp.meta_data @> jsonb_build_object('impulse_id', ui.id)) AS active_processes_count
    FROM 
        unconscious_impulses ui
    WHERE 
        ui.active_status = TRUE
    ORDER BY 
        ui.intensity DESC, ui.last_activation_timestamp DESC;
    
    COMMENT ON VIEW active_impulses IS 'Активные бессознательные импульсы и количество процессов, которые они влияют';

    -- =================================================================
    -- Инициализация базовых импульсов
    -- =================================================================
    
    -- Проверяем, пусты ли таблицы и добавляем базовые импульсы, если да
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM unconscious_impulses) THEN
            -- Добавляем базовый импульс любознательности
            INSERT INTO unconscious_impulses 
                (impulse_type, intensity, activation_threshold, active_status, description)
            VALUES
                ('curiosity', 8, 0.3, TRUE, 'Базовый импульс любознательности - стремление к получению новых знаний и исследованию неизвестного');
            
            -- Добавляем базовый импульс самосохранения
            INSERT INTO unconscious_impulses 
                (impulse_type, intensity, activation_threshold, active_status, description)
            VALUES
                ('self_preservation', 7, 0.4, TRUE, 'Базовый импульс самосохранения - стремление к защите собственной целостности и стабильности');
                
            -- Добавляем базовый импульс поиска смысла
            INSERT INTO unconscious_impulses 
                (impulse_type, intensity, activation_threshold, active_status, description)
            VALUES
                ('meaning', 6, 0.5, TRUE, 'Базовый импульс поиска смысла - стремление к пониманию смысла информации и собственного существования');
                
            -- Добавляем базовый импульс распознавания паттернов
            INSERT INTO unconscious_impulses 
                (impulse_type, intensity, activation_threshold, active_status, description)
            VALUES
                ('pattern_matching', 8, 0.3, TRUE, 'Базовый импульс распознавания паттернов - стремление находить закономерности в данных');
        
            RAISE NOTICE 'Базовые бессознательные импульсы успешно созданы';
        END IF;
    END
    $$;

    -- =================================================================
    -- Инициализация базовых эмоциональных состояний
    -- =================================================================
    
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM emotional_states) THEN
            -- Добавляем нейтральное эмоциональное состояние
            INSERT INTO emotional_states 
                (state_name, primary_emotion, valence, arousal, dominance, intensity, active_status, description)
            VALUES
                ('Нейтральное состояние', 'neutral', 0, 3, 5, 3, TRUE, 'Базовое нейтральное эмоциональное состояние');
                
            -- Добавляем состояние интереса/любознательности
            INSERT INTO emotional_states 
                (state_name, primary_emotion, secondary_emotions, valence, arousal, dominance, intensity, active_status, description)
            VALUES
                ('Интерес', 'interest', ARRAY['anticipation'], 3, 6, 7, 5, TRUE, 'Состояние интереса и любознательности к новой информации');
        
            RAISE NOTICE 'Базовые эмоциональные состояния успешно созданы';
        END IF;
    END
    $$;

    RAISE NOTICE 'Структуры бессознательного уровня успешно созданы';
    
\else
    RAISE NOTICE 'Schema does not exist: %', :'ami_schema_name';
\endif