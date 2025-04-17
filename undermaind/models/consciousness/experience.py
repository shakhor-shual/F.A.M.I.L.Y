"""
Модель для хранения опыта/воспоминаний АМИ.

Этот модуль определяет центральную модель уровня сознания - Experience,
которая представляет собой отдельные элементы опыта АМИ (воспоминания).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, TEXT, Boolean, TIMESTAMP, SmallInteger, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from undermaind.models.base import Base
from undermaind.models.consciousness.experience_sources import ExperienceSource
from undermaind.models.consciousness.experience_contexts import ExperienceContext


class Experience(Base):
    """
    Модель опыта/воспоминания АМИ.
    
    Представляет собой отдельный элемент опыта АМИ, который может быть:
    - Восприятием (входящая информация)
    - Мыслью (результат обработки)
    - Действием (исходящая активность)
    - Коммуникацией (взаимодействие)
    """
    __tablename__ = 'experiences'

    # Указываем явно схему для таблицы
    __table_args__ = (
        CheckConstraint(
            "information_category IN ('self', 'subject', 'object')",
            name='valid_information_category'
        ),
        CheckConstraint(
            "experience_type IN ('perception', 'thought', 'action', 'communication', 'reflection', 'emotion', 'memory', 'insight', 'other')",
            name='valid_experience_type'
        ),
        CheckConstraint(
            "subjective_position IN ('addressee', 'addresser', 'observer', 'reflective')",
            name='valid_subjective_position'
        ),
        CheckConstraint(
            "communication_direction IN ('incoming', 'outgoing') OR communication_direction IS NULL",
            name='valid_communication_direction'
        ),
        CheckConstraint(
            "provenance_type IN ('identified', 'provisional', 'system_generated')",
            name='valid_provenance_type'
        ),
        CheckConstraint(
            'salience BETWEEN 1 AND 10',
            name='valid_salience_range'
        ),
        {'schema': 'ami_test_user'}  # Схема должна соответствовать имени АМИ
    )

    # Основные поля
    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now)
    
    # Категоризация опыта
    information_category = Column(String, nullable=False)
    experience_type = Column(String, nullable=False)
    subjective_position = Column(String, nullable=False)
    communication_direction = Column(String)
    
    # Содержание
    content = Column(TEXT, nullable=False)
    content_vector = Column(Vector(1536))
    
    # Связи с контекстом и источниками
    context_id = Column(Integer, ForeignKey('experience_contexts.id', name='fk_experience_context'))
    provisional_context = Column(TEXT)
    source_id = Column(Integer, ForeignKey('experience_sources.id', name='fk_experience_source'))
    provisional_source = Column(TEXT)
    target_id = Column(Integer, ForeignKey('experience_sources.id', name='fk_experience_target'))
    
    # Базовые атрибуты
    salience = Column(
        SmallInteger, 
        CheckConstraint(
            'salience BETWEEN 1 AND 10',
            name='check_salience_range'
        ), 
        default=5
    )
    provenance_type = Column(String, nullable=False, default='identified')
    verified_status = Column(Boolean, default=False)
    
    # Связи с другими опытами
    parent_experience_id = Column(Integer, ForeignKey('experiences.id', name='fk_experience_parent'))
    response_to_experience_id = Column(Integer, ForeignKey('experiences.id', name='fk_experience_response'))
    thinking_process_id = Column(Integer)  # Будет внешним ключом к таблице thinking_processes
    emotional_evaluation_id = Column(Integer)  # Будет внешним ключом к таблице в подсознательном уровне
    
    # Метаданные
    meta_data = Column(JSONB)
    
    # Отношения
    context = relationship('ExperienceContext', foreign_keys=[context_id])
    source = relationship('ExperienceSource', foreign_keys=[source_id])
    target = relationship('ExperienceSource', foreign_keys=[target_id])
    
    parent_experience = relationship(
        'Experience',
        foreign_keys=[parent_experience_id],
        remote_side=[id],
        backref='child_experiences'
    )
    
    response_to = relationship(
        'Experience',
        foreign_keys=[response_to_experience_id],
        remote_side=[id],
        backref='responses'
    )

    # Связи с другими моделями
    attributes = relationship('ExperienceAttribute', back_populates='experience', cascade='all, delete-orphan')
    outgoing_connections = relationship(
        'ExperienceConnection',
        foreign_keys='ExperienceConnection.source_experience_id',
        back_populates='source_experience',
        cascade='all, delete-orphan'
    )
    incoming_connections = relationship(
        'ExperienceConnection',
        foreign_keys='ExperienceConnection.target_experience_id',
        back_populates='target_experience',
        cascade='all, delete-orphan'
    )

    # Константы для категорий информации
    CATEGORY_SELF = 'self'     # Категория "Я"
    CATEGORY_SUBJECT = 'subject'  # Категория "Ты"
    CATEGORY_OBJECT = 'object'    # Категория "Оно"

    # Константы для типов опыта
    TYPE_PERCEPTION = 'perception'       # Восприятие
    TYPE_THOUGHT = 'thought'            # Мысль
    TYPE_ACTION = 'action'              # Действие
    TYPE_COMMUNICATION = 'communication' # Коммуникация
    TYPE_REFLECTION = 'reflection'       # Рефлексия
    TYPE_EMOTION = 'emotion'            # Эмоция
    TYPE_MEMORY = 'memory'              # Воспоминание
    TYPE_INSIGHT = 'insight'            # Инсайт
    TYPE_OTHER = 'other'                # Другой тип

    # Константы для субъективных позиций
    POSITION_ADDRESSEE = 'addressee'     # Адресат
    POSITION_ADDRESSER = 'addresser'     # Адресант
    POSITION_OBSERVER = 'observer'       # Наблюдатель
    POSITION_REFLECTIVE = 'reflective'   # Рефлексирующий

    # Константы для направления коммуникации
    DIRECTION_INCOMING = 'incoming'      # Входящая
    DIRECTION_OUTGOING = 'outgoing'      # Исходящая

    # Константы для типов происхождения
    PROVENANCE_IDENTIFIED = 'identified'         # Полностью идентифицированный
    PROVENANCE_PROVISIONAL = 'provisional'       # С временными данными
    PROVENANCE_SYSTEM = 'system_generated'      # Сгенерированный системой

    def __init__(self, **kwargs):
        """Инициализация нового опыта."""
        super().__init__(**kwargs)
        self.timestamp = kwargs.get('timestamp', datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'information_category': self.information_category,
            'experience_type': self.experience_type,
            'subjective_position': self.subjective_position,
            'communication_direction': self.communication_direction,
            'content': self.content,
            'context_id': self.context_id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'salience': self.salience,
            'provenance_type': self.provenance_type,
            'verified_status': self.verified_status,
            'parent_experience_id': self.parent_experience_id,
            'response_to_experience_id': self.response_to_experience_id,
            'thinking_process_id': self.thinking_process_id,
            'emotional_evaluation_id': self.emotional_evaluation_id
        }

    def __repr__(self) -> str:
        """Строковое представление опыта."""
        return f"<Experience(id={self.id}, type='{self.experience_type}', category='{self.information_category}')>"

    @classmethod
    def create(cls, session, content: str, information_category: str, 
               experience_type: str, subjective_position: str, **kwargs) -> 'Experience':
        """
        Создает новый опыт с указанными базовыми параметрами.
        
        Args:
            session: Сессия SQLAlchemy
            content: Содержание опыта
            information_category: Категория информации (self/subject/object)
            experience_type: Тип опыта
            subjective_position: Субъективная позиция
            **kwargs: Дополнительные параметры опыта
        
        Returns:
            Experience: Созданный объект опыта
        """
        experience = cls(
            content=content,
            information_category=information_category,
            experience_type=experience_type,
            subjective_position=subjective_position,
            **kwargs
        )
        session.add(experience)
        session.flush()  # Получаем ID без коммита
        return experience

    @classmethod
    def get_by_id(cls, session, experience_id: int) -> Optional['Experience']:
        """
        Получает опыт по его ID.
        
        Args:
            session: Сессия SQLAlchemy
            experience_id: ID опыта
            
        Returns:
            Optional[Experience]: Найденный опыт или None
        """
        return session.query(cls).filter(cls.id == experience_id).first()

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты опыта.
        
        Args:
            **kwargs: Пары ключ-значение для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def is_provisional(self) -> bool:
        """Проверяет, является ли опыт временным."""
        return self.provenance_type == self.PROVENANCE_PROVISIONAL

    @property
    def has_context(self) -> bool:
        """Проверяет, привязан ли опыт к контексту."""
        return self.context_id is not None

    @property
    def has_source(self) -> bool:
        """Проверяет, привязан ли опыт к источнику."""
        return self.source_id is not None