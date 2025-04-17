"""
Модель для источников опыта АМИ.

Этот модуль определяет модель SQLAlchemy для таблицы experience_sources,
которая хранит информацию об источниках опыта (агентивных и неагентивных).
"""

from sqlalchemy import Column, Integer, String, TEXT, Boolean, TIMESTAMP, SmallInteger, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional, List, Dict, Any

from undermaind.models.base import Base


class ExperienceSource(Base):
    """
    Модель источника опыта АМИ.
    
    Источник опыта - это сущность, с которой взаимодействует АМИ. Может быть:
    - Агентивным источником (человек, другой ИИ) - категория "Ты"
    - Неагентивным источником (ресурс, система) - категория "Оно"
    - Сам АМИ - категория "Я"
    """
    __tablename__ = 'experience_sources'
    
    # Используем схему, соответствующую имени АМИ
    __table_args__ = {'schema': 'ami_test_user'}
    
    # Основные поля
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    information_category = Column(String, nullable=False)
    agency_level = Column(SmallInteger, default=0)
    
    # Метаданные взаимодействия
    first_interaction = Column(TIMESTAMP(timezone=True), default=datetime.now)
    last_interaction = Column(TIMESTAMP(timezone=True), default=datetime.now)
    interaction_count = Column(Integer, default=1)
    is_ephemeral = Column(Boolean, default=False)
    provisional_data = Column(JSONB)
    
    # Поля для агентивных источников
    familiarity_level = Column(SmallInteger)
    trust_level = Column(SmallInteger)
    
    # Поля для неагентивных источников
    uri = Column(TEXT)
    content_hash = Column(String)
    resource_type = Column(String)
    
    # Общие данные
    description = Column(TEXT)
    related_experiences = Column(ARRAY(Integer))
    meta_data = Column(JSONB)
    
    # Константы для типов источников
    SOURCE_TYPE_HUMAN = 'human'
    SOURCE_TYPE_AMI = 'ami'
    SOURCE_TYPE_SYSTEM = 'system'
    SOURCE_TYPE_RESOURCE = 'resource'
    SOURCE_TYPE_SELF = 'self'
    SOURCE_TYPE_HYBRID = 'hybrid'
    SOURCE_TYPE_OTHER = 'other'
    
    # Константы для категорий
    CATEGORY_SELF = 'self'
    CATEGORY_SUBJECT = 'subject'
    CATEGORY_OBJECT = 'object'
    CATEGORY_AMBIGUOUS = 'ambiguous'
    
    # Константы для типов ресурсов
    RESOURCE_TYPE_FILE = 'file'
    RESOURCE_TYPE_WEBPAGE = 'webpage'
    RESOURCE_TYPE_API = 'api'
    RESOURCE_TYPE_DATABASE = 'database'
    RESOURCE_TYPE_SERVICE = 'service'
    RESOURCE_TYPE_OTHER = 'other'
    
    @classmethod
    def get_or_create_unknown_source(cls, session) -> 'ExperienceSource':
        """
        Получает или создает запись для неизвестного источника опыта.
        
        Args:
            session: Сессия SQLAlchemy
            
        Returns:
            ExperienceSource: Экземпляр неизвестного источника
        """
        unknown_source = session.query(cls).filter(
            cls.name == 'UNKNOWN',
            cls.source_type == cls.SOURCE_TYPE_OTHER
        ).first()
        
        if not unknown_source:
            unknown_source = cls(
                name='UNKNOWN',
                source_type=cls.SOURCE_TYPE_OTHER,
                information_category=cls.CATEGORY_AMBIGUOUS,
                agency_level=0,
                is_ephemeral=True,
                familiarity_level=0,
                trust_level=0,
                description='Неидентифицированный источник опыта'
            )
            session.add(unknown_source)
            session.flush()
            
        return unknown_source
    
    @classmethod
    def get_or_create_self_source(cls, session) -> 'ExperienceSource':
        """
        Получает или создает запись для самого АМИ.
        
        Args:
            session: Сессия SQLAlchemy
            
        Returns:
            ExperienceSource: Экземпляр источника, представляющего АМИ
        """
        self_source = session.query(cls).filter(
            cls.name == 'self',
            cls.source_type == cls.SOURCE_TYPE_SELF
        ).first()
        
        if not self_source:
            self_source = cls(
                name='self',
                source_type=cls.SOURCE_TYPE_SELF,
                information_category=cls.CATEGORY_SELF,
                agency_level=10,
                familiarity_level=10,
                trust_level=5,
                description='Я - АМИ, Artifical Mind Identity'
            )
            session.add(self_source)
            session.flush()
            
        return self_source
    
    @classmethod
    def create(cls, session, name: str, source_type: str, 
               information_category: str, **kwargs) -> 'ExperienceSource':
        """
        Создает новый источник опыта.
        
        Args:
            session: Сессия SQLAlchemy
            name: Имя источника
            source_type: Тип источника
            information_category: Категория информации
            **kwargs: Дополнительные параметры
            
        Returns:
            ExperienceSource: Созданный источник опыта
        """
        source = cls(
            name=name,
            source_type=source_type,
            information_category=information_category,
            **kwargs
        )
        session.add(source)
        session.flush()
        return source

    @classmethod
    def get_by_id(cls, session, source_id: int) -> Optional['ExperienceSource']:
        """
        Получает источник по его ID.
        
        Args:
            session: Сессия SQLAlchemy
            source_id: ID источника
            
        Returns:
            Optional[ExperienceSource]: Найденный источник или None
        """
        return session.query(cls).filter(cls.id == source_id).first()
    
    @classmethod
    def find_by_name(cls, session, name: str) -> Optional['ExperienceSource']:
        """
        Ищет источник по имени.
        
        Args:
            session: Сессия SQLAlchemy
            name: Имя источника
            
        Returns:
            Optional[ExperienceSource]: Найденный источник или None
        """
        return session.query(cls).filter(cls.name == name).first()

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты источника.
        
        Args:
            **kwargs: Пары ключ-значение для обновления
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Автоматически обновляем метрики взаимодействия
        self.update_interaction_metrics()
    
    def update_interaction_metrics(self):
        """Обновляет метрики взаимодействия с источником."""
        self.last_interaction = datetime.now()
        self.interaction_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует модель в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'information_category': self.information_category,
            'agency_level': self.agency_level,
            'first_interaction': self.first_interaction,
            'last_interaction': self.last_interaction,
            'interaction_count': self.interaction_count,
            'is_ephemeral': self.is_ephemeral,
            'familiarity_level': self.familiarity_level,
            'trust_level': self.trust_level,
            'uri': self.uri,
            'resource_type': self.resource_type,
            'description': self.description
        }
        
    def __repr__(self) -> str:
        return f"<ExperienceSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"