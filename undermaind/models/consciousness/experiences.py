"""
Модель опыта/переживаний АМИ в проекте F.A.M.I.L.Y.
Центральная сущность сознательного уровня памяти АМИ.
"""

from sqlalchemy import Column, Integer, String, Text, SmallInteger, TIMESTAMP, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from ..base import Base
from undermaind.core.vectors import Vector
import enum


class ExperienceType(str, enum.Enum):
    """Типы происхождения опыта с точки зрения определенности источника."""
    IDENTIFIED = 'identified'       # Полностью определенный опыт
    PROVISIONAL = 'provisional'     # Временный, не полностью определенный опыт
    SYSTEM_GENERATED = 'system'     # Опыт, сгенерированный системой


class ExperienceCategory(str, enum.Enum):
    """Категории информации в опыте с точки зрения отношения к АМИ."""
    SELF = 'self'      # Категория "Я" - относящаяся к самому АМИ
    AGENT = 'agent'    # Категория "Ты" - относящаяся к внешнему агенту/человеку
    OBJECT = 'object'  # Категория "Оно" - относящаяся к внешнему объекту/ресурсу


class Experience(Base):
    """
    Модель опыта/переживаний - центральная таблица сознательного уровня памяти АМИ.
    Представляет все информационные события, оставляющие след в сознании.
    """
    __tablename__ = 'experiences'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default='CURRENT_TIMESTAMP')
    context_id = Column(Integer, ForeignKey('memory_contexts.id'), nullable=True)  # Может быть NULL при временном контексте
    information_category = Column(String, nullable=False)
    experience_type = Column(String, nullable=False)
    sender_participant_id = Column(Integer, ForeignKey('participants.id'), nullable=True)  # Может быть NULL при временном отправителе
    to_participant_id = Column(Integer, ForeignKey('participants.id'))
    content = Column(Text, nullable=False)
    content_vector = Column(Vector(1536))
    salience = Column(SmallInteger, default=5)
    emotional_valence = Column(SmallInteger, default=0)
    emotional_intensity = Column(SmallInteger, default=0)
    verified_status = Column(Boolean, default=False)
    parent_experience_id = Column(Integer, ForeignKey('experiences.id'))
    response_to_experience_id = Column(Integer, ForeignKey('experiences.id'))
    meta_data = Column(JSONB)
    
    # Поля для решения "Парадокса первичности"
    provenance_type = Column(Enum(ExperienceType), default=ExperienceType.IDENTIFIED)
    provisional_sender = Column(String)  # Строковое описание отправителя, когда сущность еще не существует
    provisional_context = Column(String)  # Строковое описание контекста, когда сущность еще не существует
    
    # Отношения будут определены централизованно в __init__.py
    
    def __repr__(self):
        return f"<Experience(id={self.id}, type='{self.experience_type}', category='{self.information_category}')>"
    
    @hybrid_property
    def effective_sender(self):
        """
        Возвращает либо связанного отправителя, либо временное описание отправителя.
        Это гибридное свойство обеспечивает прозрачный доступ к информации об отправителе.
        """
        # Будет реализовано через отношения в __init__.py
        # Временное решение для согласованности интерфейса
        return self.sender_participant_id or self.provisional_sender
    
    @hybrid_property
    def effective_context(self):
        """
        Возвращает либо связанный контекст, либо временное описание контекста.
        Это гибридное свойство обеспечивает прозрачный доступ к информации о контексте.
        """
        # Будет реализовано через отношения в __init__.py
        # Временное решение для согласованности интерфейса
        return self.context_id or self.provisional_context