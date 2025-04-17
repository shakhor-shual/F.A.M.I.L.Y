"""
Модель расширенных атрибутов опыта АМИ.

Этот модуль определяет модель SQLAlchemy для таблицы experience_attributes,
которая позволяет добавлять произвольные атрибуты к опыту без изменения
основной схемы таблицы experiences.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, TEXT, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from undermaind.models.base import Base
from undermaind.models.consciousness.experience import Experience

class ExperienceAttribute(Base):
    """
    Модель расширенного атрибута опыта АМИ.
    
    Позволяет добавлять произвольные атрибуты к опыту в формате:
    - Название атрибута
    - Значение атрибута
    - Тип данных атрибута
    """
    __tablename__ = 'experience_attributes'
    __table_args__ = (
        CheckConstraint(
            "attribute_type IN ('string', 'number', 'boolean', 'datetime', "
            "'json', 'other')",
            name='valid_attribute_type'
        ),
        {'schema': 'ami_test_user'}
    )

    # Основные поля
    id = Column(Integer, primary_key=True)
    experience_id = Column(Integer, ForeignKey('ami_test_user.experiences.id'), nullable=False)
    attribute_name = Column(String, nullable=False)
    attribute_value = Column(TEXT, nullable=False)
    attribute_type = Column(String, default='string')
    
    # Метаданные
    meta_data = Column(JSONB)
    
    # Отношения
    experience = relationship('Experience', back_populates='attributes')

    # Константы для типов атрибутов
    TYPE_STRING = 'string'
    TYPE_NUMBER = 'number'
    TYPE_BOOLEAN = 'boolean'
    TYPE_DATETIME = 'datetime'
    TYPE_JSON = 'json'
    TYPE_OTHER = 'other'

    @classmethod
    def create(cls, session, experience_id: int, attribute_name: str, 
               attribute_value: str, **kwargs) -> 'ExperienceAttribute':
        """
        Создает новый атрибут опыта.
        
        Args:
            session: Сессия SQLAlchemy
            experience_id: ID опыта
            attribute_name: Название атрибута
            attribute_value: Значение атрибута
            **kwargs: Дополнительные параметры
            
        Returns:
            ExperienceAttribute: Созданный атрибут
        """
        attribute = cls(
            experience_id=experience_id,
            attribute_name=attribute_name,
            attribute_value=attribute_value,
            **kwargs
        )
        session.add(attribute)
        session.flush()
        return attribute

    @classmethod
    def get_by_id(cls, session, attribute_id: int) -> Optional['ExperienceAttribute']:
        """
        Получает атрибут по ID.
        
        Args:
            session: Сессия SQLAlchemy
            attribute_id: ID атрибута
            
        Returns:
            Optional[ExperienceAttribute]: Найденный атрибут или None
        """
        return session.query(cls).filter(cls.id == attribute_id).first()

    @classmethod
    def get_experience_attributes(cls, session, experience_id: int) -> List['ExperienceAttribute']:
        """
        Получает все атрибуты опыта.
        
        Args:
            session: Сессия SQLAlchemy
            experience_id: ID опыта
            
        Returns:
            List[ExperienceAttribute]: Список атрибутов
        """
        return session.query(cls).filter(cls.experience_id == experience_id).all()

    @classmethod
    def find_by_name(cls, session, experience_id: int, 
                     attribute_name: str) -> Optional['ExperienceAttribute']:
        """
        Ищет атрибут по имени для конкретного опыта.
        
        Args:
            session: Сессия SQLAlchemy
            experience_id: ID опыта
            attribute_name: Название атрибута
            
        Returns:
            Optional[ExperienceAttribute]: Найденный атрибут или None
        """
        return session.query(cls).filter(
            cls.experience_id == experience_id,
            cls.attribute_name == attribute_name
        ).first()

    @classmethod
    def find_by_value(cls, session, attribute_value: str) -> List['ExperienceAttribute']:
        """
        Ищет атрибуты по значению.
        
        Args:
            session: Сессия SQLAlchemy
            attribute_value: Значение атрибута
            
        Returns:
            List[ExperienceAttribute]: Список найденных атрибутов
        """
        return session.query(cls).filter(cls.attribute_value == attribute_value).all()

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты.
        
        Args:
            **kwargs: Пары ключ-значение для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            'id': self.id,
            'experience_id': self.experience_id,
            'attribute_name': self.attribute_name,
            'attribute_value': self.attribute_value,
            'attribute_type': self.attribute_type,
            'meta_data': self.meta_data
        }

    def __repr__(self) -> str:
        return (f"<ExperienceAttribute(id={self.id}, name='{self.attribute_name}', "
                f"type='{self.attribute_type}', value='{self.attribute_value[:20]}...')>")