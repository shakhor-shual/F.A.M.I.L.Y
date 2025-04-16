Вот структурированный MD-файл с инструкциями по реализации SQLAlchemy ORM для вашей схемы, оптимизированный для избежания циклических импортов:

markdown
Copy
# SQLAlchemy ORM Implementation Guide for F.A.M.I.L.Y. Project

## Структура проекта
models/
├── init.py # Экспорт всех моделей и общих зависимостей
├── base.py # Базовый класс и общие настройки
├── participant.py # Модель Participant
├── memory_context.py # Модель MemoryContext
├── experience.py # Модель Experience (центральная)
├── thought_chain.py # Модель ThoughtChain
├── information_resource.py # Модель InformationResource
└── experience_connection.py # Модель ExperienceConnection

Copy

## 1. Базовый конфигурационный файл (`base.py`)
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Специальное соглашение для именования constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

# Общие типы и утилиты могут быть добавлены здесь
2. Модель Participant (participant.py)
python
Copy
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, TIMESTAMP
from .base import Base

class Participant(Base):
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    participant_type = Column(String(20), nullable=False)
    # ... остальные поля без прямых ссылок на другие модели
    
    # Отношения будут определены в __init__.py
    # Это предотвращает циклические импорты
3. Модель MemoryContext (memory_context.py)
python
Copy
from sqlalchemy import Column, Integer, String, Text, ARRAY, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class MemoryContext(Base):
    __tablename__ = 'memory_contexts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    context_type = Column(String(30), nullable=False)
    # ... остальные поля
    
    # Родительский контекст использует строковую ссылку
    parent_context_id = Column(Integer, ForeignKey('memory_contexts.id'))
4. Модель Experience (experience.py)
python
Copy
from sqlalchemy import Column, Integer, String, Text, SmallInteger, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class Experience(Base):
    __tablename__ = 'experiences'
    
    id = Column(Integer, primary_key=True)
    context_id = Column(Integer, ForeignKey('memory_contexts.id'))
    sender_participant_id = Column(Integer, ForeignKey('participants.id'))
    to_participant_id = Column(Integer, ForeignKey('participants.id'))
    # ... остальные поля
    
    # Самореферентные связи
    parent_experience_id = Column(Integer, ForeignKey('experiences.id'))
    response_to_experience_id = Column(Integer, ForeignKey('experiences.id'))
5. Инициализация отношений в __init__.py
python
Copy
from .base import Base
from .participant import Participant
from .memory_context import MemoryContext
from .experience import Experience
from .thought_chain import ThoughtChain
from .information_resource import InformationResource
from .experience_connection import ExperienceConnection

def setup_relationships():
    # Участник
    Participant.sent_experiences = relationship(
        "Experience", 
        foreign_keys="[Experience.sender_participant_id]",
        back_populates="sender"
    )
    
    Participant.received_experiences = relationship(
        "Experience",
        foreign_keys="[Experience.to_participant_id]",
        back_populates="recipient"
    )
    
    # Контекст памяти
    MemoryContext.experiences = relationship(
        "Experience", 
        back_populates="context"
    )
    
    MemoryContext.child_contexts = relationship(
        "MemoryContext",
        back_populates="parent_context",
        remote_side="MemoryContext.id"
    )
    
    MemoryContext.parent_context = relationship(
        "MemoryContext",
        remote_side="MemoryContext.id",
        back_populates="child_contexts"
    )
    
    # Опыт
    Experience.sender = relationship(
        "Participant",
        foreign_keys="[Experience.sender_participant_id]",
        back_populates="sent_experiences"
    )
    
    Experience.recipient = relationship(
        "Participant",
        foreign_keys="[Experience.to_participant_id]",
        back_populates="received_experiences"
    )
    
    # ... другие отношения

# Инициализация всех моделей
__all__ = [
    'Base',
    'Participant',
    'MemoryContext',
    'Experience',
    'ThoughtChain',
    'InformationResource',
    'ExperienceConnection',
    'setup_relationships'
]
6. Инициализация базы данных
python
Copy
# В файле database.py
from sqlalchemy import create_engine
from models import Base, setup_relationships

engine = create_engine('postgresql://user:pass@localhost/dbname')

def init_db():
    # Сначала создаем все таблицы
    Base.metadata.create_all(engine)
    
    # Затем устанавливаем отношения
    setup_relationships()
Правила работы с моделями
Импорт моделей:
Всегда импортируйте модели через models:

python
Copy
from models import Participant, Experience
Избегание прямых импортов:
Никогда не делайте прямые импорты между файлами моделей:

python
Copy
# ПЛОХО: в participant.py
from .experience import Experience
Отложенные отношения:
Все отношения определяются строковыми ссылками:

python
Copy
# ХОРОШО:
children = relationship("ChildModel", back_populates="parent")
Тестирование:
Используйте фикстуры для тестов:

python
Copy
@pytest.fixture
def db_session():
    from database import engine, Session
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
Решение проблем
Если возникает ImportError:

Убедитесь, что все отношения используют строковые ссылки

Проверьте порядок импорта в models/__init__.py

Для сложных случаев используйте sqlalchemy.orm.backref:

python
Copy
from sqlalchemy.orm import backref

parent = relationship("Parent", backref=backref("children", lazy="dynamic"))
Эта структура гарантирует:

Отсутствие циклических импортов

Четкое разделение ответственности

Легкую масштабируемость модели

Copy

Это руководство можно прямо передать Copilot или другим ИИ-ассистентам для реализации ORM-слоя. Ключевые особенности:
1. Все отношения вынесены в централизованный `setup_relationships()`
2. Используются только строковые ссылки на модели
3. Четкое разделение инициализации БД и определения моделей
4. Готовые решения для тестирования