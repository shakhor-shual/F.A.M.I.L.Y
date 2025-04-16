-- ============================================================================
-- ПРОЦЕДУРА СОЗДАНИЯ СТРУКТУРЫ ОПЫТА СОЗНАТЕЛЬНОГО УРОВНЯ
-- ============================================================================
-- Создает центральную таблицу experiences и вспомогательную таблицу атрибутов:
-- 1. Опыт/переживания (experiences)
-- 2. Атрибуты опыта (experience_attributes)
-- ============================================================================

CREATE OR REPLACE PROCEDURE public.create_ami_experience_structure(schema_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- =================================================================
    -- Таблица для хранения основных воспоминаний (опыта)
    -- Центральная таблица сознательного уровня памяти АМИ
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experiences (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        -- Категоризация опыта (обязательные поля)
        information_category TEXT NOT NULL CHECK (information_category IN (
            ''self'',    -- Категория "Я" (информация от самого себя)
            ''subject'', -- Категория "Ты" (информация от агентивного источника)
            ''object''   -- Категория "Оно" (информация от неагентивного источника)
        )),
        
        -- Базовое деление опыта по типу (что это?)
        experience_type TEXT NOT NULL CHECK (experience_type IN (
            ''perception'',       -- Восприятие (входящая информация)
            ''thought'',          -- Мысль
            ''action'',           -- Действие АМИ
            ''communication'',    -- Коммуникация (входящая или исходящая)
            ''decision'',         -- Принятие решения
            ''memory_recall'',    -- Воспоминание
            ''insight''           -- Инсайт/озарение
        )),
        
        -- Субъективная позиция АМИ в опыте
        subjective_position TEXT NOT NULL CHECK (subjective_position IN (
            ''addressee'',      -- АМИ как адресат
            ''addresser'',      -- АМИ как адресант
            ''observer'',       -- АМИ как наблюдатель
            ''reflective''      -- АМИ в рефлексивном режиме
        )),
        
        -- Направление коммуникации
        communication_direction TEXT CHECK (communication_direction IN (
            ''incoming'',     -- Входящая коммуникация
            ''outgoing''      -- Исходящая коммуникация
        )),
        
        -- Контекст
        context_id INTEGER REFERENCES %I.experience_contexts(id),
        provisional_context TEXT,
        
        -- Связи с источниками опыта
        source_id INTEGER REFERENCES %I.experience_sources(id),
        provisional_source TEXT,
        target_id INTEGER REFERENCES %I.experience_sources(id),
        
        -- Основное содержание
        content TEXT NOT NULL,
        content_vector vector(1536),
        
        -- Базовые атрибуты опыта
        salience SMALLINT CHECK (salience BETWEEN 1 AND 10) DEFAULT 5,
        provenance_type TEXT NOT NULL CHECK (provenance_type IN (
            ''identified'',      -- Полностью идентифицированный опыт
            ''provisional'',      -- Опыт с временными данными
            ''system_generated''  -- Опыт, сгенерированный системой
        )) DEFAULT ''identified'',
        verified_status BOOLEAN DEFAULT FALSE,
        
        -- Связи с другими опытами
        parent_experience_id INTEGER REFERENCES %I.experiences(id),
        response_to_experience_id INTEGER REFERENCES %I.experiences(id),
        thinking_process_id INTEGER,
        
        -- Связь с подсознательным уровнем
        emotional_evaluation_id INTEGER,
        
        -- Метаданные
        meta_data JSONB
    )', schema_name, schema_name, schema_name, schema_name, schema_name, schema_name);
    
    -- Комментарии к таблице experience
    EXECUTE format('COMMENT ON TABLE %I.experiences IS $c$Центральная таблица опыта/переживаний АМИ - все информационные события, оставляющие след в сознании$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.information_category IS $c$Субъективная категория источника информации: Я (self), Ты (subject), Оно (object)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.experience_type IS $c$Тип опыта: восприятие, мысль, действие и т.д.$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.subjective_position IS $c$Субъективная позиция АМИ в опыте: адресат, адресант, наблюдатель или рефлексирующий$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.communication_direction IS $c$Направление коммуникации: входящая или исходящая (для типа communication)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.provenance_type IS $c$Тип происхождения опыта: идентифицированный, временный, сгенерированный системой$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.provisional_context IS $c$Текстовое описание контекста, когда полноценная запись в таблице experience_contexts еще не создана$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.provisional_source IS $c$Текстовое описание источника, когда полноценная запись в таблице experience_sources еще не создана$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.salience IS $c$Субъективная значимость опыта по шкале 1-10$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.parent_experience_id IS $c$Ссылка на родительский опыт (для иерархии)$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.response_to_experience_id IS $c$Ссылка на опыт, на который это является ответом$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.thinking_process_id IS $c$Ссылка на процесс мышления, который привел к данному опыту$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experiences.emotional_evaluation_id IS $c$Ссылка на эмоциональную оценку опыта из подсознательного уровня$c$', schema_name);

    -- Создание индексов для воспоминаний
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_timestamp_idx ON %I.experiences(timestamp)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_context_id_idx ON %I.experiences(context_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_information_category_idx ON %I.experiences(information_category)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_experience_type_idx ON %I.experiences(experience_type)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_subjective_position_idx ON %I.experiences(subjective_position)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_source_id_idx ON %I.experiences(source_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_target_id_idx ON %I.experiences(target_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_salience_idx ON %I.experiences(salience)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_parent_experience_idx ON %I.experiences(parent_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_response_to_idx ON %I.experiences(response_to_experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_thinking_process_idx ON %I.experiences(thinking_process_id)', schema_name);

    -- Динамическое определение правильного оператора для индекса
    BEGIN
        -- Пробуем использовать оператор для новых версий pgvector
        EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_content_vector_idx ON %I.experiences USING ivfflat (content_vector cosine_ops)', schema_name);
    EXCEPTION
        WHEN undefined_object THEN
            BEGIN
                -- Пробуем использовать оператор для старых версий pgvector
                EXECUTE format('CREATE INDEX IF NOT EXISTS experiences_content_vector_idx ON %I.experiences USING ivfflat (content_vector vector_cosine_ops)', schema_name);
            EXCEPTION
                WHEN undefined_object THEN
                    RAISE NOTICE 'Не удалось создать индекс для векторного поля - ни cosine_ops, ни vector_cosine_ops не определены';
            END;
    END;
    
    -- =================================================================
    -- Таблица для хранения расширенных атрибутов опыта (EAV-модель)
    -- Позволяет добавлять произвольные атрибуты к любому опыту
    -- =================================================================
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.experience_attributes (
        id SERIAL PRIMARY KEY,
        experience_id INTEGER NOT NULL REFERENCES %I.experiences(id),
        attribute_name TEXT NOT NULL,
        attribute_value TEXT NOT NULL,
        attribute_type TEXT CHECK (attribute_type IN (
            ''string'', ''number'', ''boolean'', ''datetime'', ''json'', ''other''
        )) DEFAULT ''string'',
        meta_data JSONB
    )', schema_name, schema_name);
    
    -- Комментарии к таблице experience_attributes
    EXECUTE format('COMMENT ON TABLE %I.experience_attributes IS $c$Расширенные атрибуты опыта - позволяют добавлять произвольные данные к опыту без изменения основной схемы$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_attributes.attribute_name IS $c$Название атрибута - должно быть осмысленным для данного типа опыта$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_attributes.attribute_value IS $c$Значение атрибута в текстовом представлении$c$', schema_name);
    EXECUTE format('COMMENT ON COLUMN %I.experience_attributes.attribute_type IS $c$Тип данных атрибута для правильной интерпретации значения$c$', schema_name);
    
    -- Создание индексов для атрибутов
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_attributes_experience_id_idx ON %I.experience_attributes(experience_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_attributes_name_idx ON %I.experience_attributes(attribute_name)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS experience_attributes_name_value_idx ON %I.experience_attributes(attribute_name, attribute_value)', schema_name);
    
    RAISE NOTICE 'Структуры опыта успешно созданы';
END;
$$;
