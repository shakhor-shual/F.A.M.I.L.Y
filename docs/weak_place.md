Проблема в терминах онтологии:
Парадокс первичности:

Опыт (experiences) зависит от участников (participants) и контекстов (memory_contexts)

Но первый опыт о новом участнике/контексте не может ссылаться на ещё не созданные сущности

Категория "Неизвестного":

Источник опыта может быть неидентифицируемым ("анонимное сообщение")

Контекст может быть неопределённым ("спонтанная мысль")

Решение через "Деградированные состояния" (Degraded States)
1. Модификация таблицы participants:
sql
Copy
ALTER TABLE participants 
ADD COLUMN is_ephemeral BOOLEAN DEFAULT FALSE,
ADD COLUMN provisional_data JSONB; -- Временные данные до идентификации

-- Специальная запись для неизвестных участников
INSERT INTO participants (name, participant_type, is_ephemeral) 
VALUES ('UNKNOWN', 'other', TRUE);
2. Обновлённая модель Experience:
python
Copy
class Experience(Base):
    # ...
    sender_participant_id = Column(Integer, ForeignKey('participants.id'), nullable=True)
    context_id = Column(Integer, ForeignKey('memory_contexts.id'), nullable=True)
    
    # Альтернативные текстовые описания (когда сущности ещё нет)
    provisional_sender = Column(String)
    provisional_context = Column(String)
    
    @hybrid_property
    def effective_sender(self):
        return self.sender if self.sender_participant_id else self.provisional_sender
    
    @hybrid_property
    def effective_context(self):
        return self.context if self.context_id else self.provisional_context
3. Механизм "Позднего связывания":
python
Copy
def reconcile_provisional_entities(session, experience_id):
    """Преобразует временные данные в полноценные сущности"""
    exp = session.query(Experience).get(experience_id)
    
    if exp.provisional_sender and not exp.sender_participant_id:
        participant = Participant(
            name=exp.provisional_sender,
            participant_type='human', # или анализ для определения типа
            is_ephemeral=False
        )
        session.add(participant)
        session.flush()
        exp.sender_participant_id = participant.id
        exp.provisional_sender = None
    
    # Аналогично для контекста
Архитектурные паттерны:
Двухфазное сохранение:

python
Copy
# Фаза 1: Сохранение опыта с временными данными
new_exp = Experience(
    content="Сообщение от неизвестного",
    provisional_sender="Аноним",
    provisional_context="Случайное взаимодействие"
)
session.add(new_exp)
session.commit()

# Фаза 2: Асинхронное уточнение
reconcile_provisional_entities.delay(new_exp.id)
Типизация "неизвестного":

python
Copy
class ExperienceType:
    IDENTIFIED = 'identified'
    PROVISIONAL = 'provisional'
    SYSTEM_GENERATED = 'system'

class Experience(Base):
    # ...
    provenance_type = Column(Enum(ExperienceType), default=ExperienceType.IDENTIFIED)
Оптимизированная ER-диаграмма:
Copy
                           +----------------+
                           |   participants |
                           +-------+--------+
                                   |
                   +---------------+---------------+
                   |                               |
           +-------+-------+           +----------+----------+
           |  experiences +----------> | memory_contexts    |
           +-------+-------+           +----------+----------+
                   |                               ^
                   |                               |
           +-------+-------+               +-------+-------+
           |  thought_     |               | information   |
           |  chains       |               | resources     |
           +---------------+               +---------------+
Правила работы с данными:
При создании опыта:

Если участник/контекст неизвестен - оставляем *_id=NULL и заполняем provisional_*

Система периодически запускает reconcile_provisional_entities

При запросах:

sql
Copy
-- Все опыты с эффективным отправителем
SELECT 
    e.id,
    COALESCE(p.name, e.provisional_sender) AS sender,
    e.content
FROM experiences e
LEFT JOIN participants p ON e.sender_participant_id = p.id;
Миграция данных:

python
Copy
# Пакетное преобразование старых данных
for exp in session.query(Experience).filter(Experience.sender_participant_id == None):
    if not exp.provisional_sender:
        exp.provisional_sender = "UNKNOWN"
    session.commit()
Это решение:

Устраняет циклические зависимости через отложенное связывание

Сохраняет целостность данных

Позволяет работать с неидентифицированными источниками

Поддерживает постепенную конкретизацию опыта

Для тестирования рекомендуем использовать моки:

python
Copy
@pytest.fixture
def provisional_experience():
    return Experience(
        content="Test",
        provisional_sender="Anonymous",
        provenance_type=ExperienceType.PROVISIONAL
    )