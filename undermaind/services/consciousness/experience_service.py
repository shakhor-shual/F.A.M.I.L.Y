"""
Сервис обработки опыта АМИ (ExperienceProcessingService).

Этот модуль реализует основную бизнес-логику для создания, обработки и управления 
опытом АМИ, являясь ключевым компонентом формирования памяти.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from undermaind.models.consciousness.experience import Experience
from undermaind.models.consciousness.experience_attribute import ExperienceAttribute
from undermaind.models.consciousness.experience_contexts import ExperienceContext
from undermaind.models.consciousness.experience_sources import ExperienceSource
from undermaind.models.consciousness.experience_connection import ExperienceConnection
from undermaind.services.base import BaseService
from undermaind.core.session import SessionManager
from undermaind.utils.vector_utils import vectorize_text

logger = logging.getLogger(__name__)


class ExperienceNotFoundError(Exception):
    """Исключение, вызываемое когда опыт не найден."""
    pass


class InvalidExperienceDataError(Exception):
    """Исключение, вызываемое при попытке создать опыт с некорректными данными."""
    pass


class AssociationError(Exception):
    """Исключение, вызываемое при ошибке создания ассоциативной связи."""
    pass


class ExperienceProcessingService(BaseService):
    """
    Сервис для обработки опыта АМИ.
    
    Этот сервис отвечает за создание, категоризацию, поиск и управление
    опытом АМИ, а также за работу с атрибутами, контекстами и источниками.
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Инициализация сервиса обработки опыта.
        
        Args:
            session_manager: Менеджер сессий для работы с БД
        """
        super().__init__(session_manager)
    
    # === Методы создания опыта ===
    
    def create_experience(self, 
                          content: str,
                          experience_type: str,
                          information_category: str,
                          subjective_position: Optional[str] = None,
                          context_id: Optional[int] = None, 
                          source_id: Optional[int] = None,
                          target_id: Optional[int] = None,
                          parent_experience_id: Optional[int] = None,
                          response_to_experience_id: Optional[int] = None,
                          communication_direction: Optional[str] = None,
                          salience: int = 5,
                          attributes: Optional[Dict[str, Any]] = None,
                          meta_data: Optional[Dict[str, Any]] = None) -> Experience:
        """
        Создание нового опыта АМИ.
        
        Args:
            content: Текстовое содержание опыта
            experience_type: Тип опыта (TYPE_PERCEPTION, TYPE_THOUGHT и т.д.)
            information_category: Категория информации (CATEGORY_SELF, CATEGORY_SUBJECT и т.д.)
            subjective_position: Субъективная позиция (POSITION_ADDRESSEE, POSITION_ADDRESSER и т.д.)
            context_id: ID контекста опыта
            source_id: ID источника опыта
            target_id: ID цели опыта (для коммуникаций)
            parent_experience_id: ID родительского опыта
            response_to_experience_id: ID опыта, на который это является ответом
            communication_direction: Направление коммуникации (DIRECTION_INCOMING, DIRECTION_OUTGOING)
            salience: Значимость опыта от 1 до 10
            attributes: Словарь атрибутов опыта
            meta_data: Дополнительные метаданные
            
        Returns:
            Experience: Созданный объект опыта
            
        Raises:
            InvalidExperienceDataError: Если данные некорректны
            SQLAlchemyError: При ошибке БД
        """
        # Проверка обязательных параметров
        if not content or not content.strip():
            raise InvalidExperienceDataError("Содержание опыта не может быть пустым")
            
        if not experience_type or not information_category:
            raise InvalidExperienceDataError("Тип опыта и категория информации обязательны")
        
        # Определение субъективной позиции по умолчанию, если не указана
        if subjective_position is None:
            if experience_type == Experience.TYPE_THOUGHT:
                subjective_position = Experience.POSITION_REFLECTIVE
            elif communication_direction == Experience.DIRECTION_INCOMING:
                subjective_position = Experience.POSITION_ADDRESSEE
            elif communication_direction == Experience.DIRECTION_OUTGOING:
                subjective_position = Experience.POSITION_ADDRESSER
            else:
                subjective_position = Experience.POSITION_OBSERVER
        
        def _create_experience_with_vector(session: Session) -> Experience:
            # Создание векторного представления содержания
            try:
                content_vector = vectorize_text(content)
            except Exception as e:
                logger.warning(f"Не удалось создать векторное представление: {e}")
                content_vector = None
            
            # Создание нового опыта
            experience = Experience(
                timestamp=datetime.now(),
                content=content,
                content_vector=content_vector,
                experience_type=experience_type,
                information_category=information_category,
                subjective_position=subjective_position,
                communication_direction=communication_direction,
                salience=salience,
                context_id=context_id,
                source_id=source_id,
                target_id=target_id,
                parent_experience_id=parent_experience_id,
                response_to_experience_id=response_to_experience_id,
                meta_data=meta_data or {}
            )
            
            session.add(experience)
            session.flush()  # Получаем ID без коммита
            
            # Добавляем атрибуты, если они переданы
            if attributes:
                for key, value in attributes.items():
                    attribute = ExperienceAttribute(
                        experience_id=experience.id,
                        attribute_key=key,
                        attribute_value=str(value)
                    )
                    session.add(attribute)
            
            return experience
        
        # Выполнение в транзакции
        return self._execute_in_transaction(_create_experience_with_vector)
    
    def create_thought_experience(self, 
                                 content: str,
                                 context_id: Optional[int] = None,
                                 thinking_process_id: Optional[int] = None,
                                 salience: int = 5,
                                 attributes: Optional[Dict[str, Any]] = None,
                                 meta_data: Optional[Dict[str, Any]] = None) -> Experience:
        """
        Создание опыта типа "мысль".
        
        Args:
            content: Содержание мысли
            context_id: ID контекста
            thinking_process_id: ID процесса мышления
            salience: Значимость от 1 до 10
            attributes: Атрибуты опыта
            meta_data: Дополнительные метаданные
            
        Returns:
            Experience: Созданный объект опыта-мысли
        """
        meta_data = meta_data or {}
        if thinking_process_id:
            meta_data['thinking_process_id'] = thinking_process_id
            
        return self.create_experience(
            content=content,
            experience_type=Experience.TYPE_THOUGHT,
            information_category=Experience.CATEGORY_SELF,
            subjective_position=Experience.POSITION_REFLECTIVE,
            context_id=context_id,
            salience=salience,
            attributes=attributes,
            meta_data=meta_data
        )
    
    def create_communication_experience(self, 
                                       content: str,
                                       is_incoming: bool,
                                       context_id: Optional[int] = None,
                                       source_id: Optional[int] = None,
                                       target_id: Optional[int] = None,
                                       salience: int = 5,
                                       attributes: Optional[Dict[str, Any]] = None,
                                       meta_data: Optional[Dict[str, Any]] = None) -> Experience:
        """
        Создание опыта типа "коммуникация".
        
        Args:
            content: Содержание коммуникации
            is_incoming: Флаг входящей коммуникации (True - входящая, False - исходящая)
            context_id: ID контекста
            source_id: ID источника (отправителя)
            target_id: ID цели (получателя)
            salience: Значимость от 1 до 10
            attributes: Атрибуты опыта
            meta_data: Дополнительные метаданные
            
        Returns:
            Experience: Созданный объект опыта-коммуникации
        """
        direction = (Experience.DIRECTION_INCOMING if is_incoming 
                    else Experience.DIRECTION_OUTGOING)
        
        position = (Experience.POSITION_ADDRESSEE if is_incoming 
                   else Experience.POSITION_ADDRESSER)
        
        return self.create_experience(
            content=content,
            experience_type=Experience.TYPE_COMMUNICATION,
            information_category=Experience.CATEGORY_SUBJECT,
            subjective_position=position,
            communication_direction=direction,
            context_id=context_id,
            source_id=source_id,
            target_id=target_id,
            salience=salience,
            attributes=attributes,
            meta_data=meta_data
        )
    
    # === Методы получения и поиска опыта ===
    
    def get_experience_by_id(self, experience_id: int) -> Experience:
        """
        Получение опыта по ID.
        
        Args:
            experience_id: ID опыта
            
        Returns:
            Experience: Объект опыта
            
        Raises:
            ExperienceNotFoundError: Если опыт не найден
        """
        def _get_experience(session: Session) -> Experience:
            experience = session.query(Experience).filter(Experience.id == experience_id).first()
            if not experience:
                raise ExperienceNotFoundError(f"Опыт с ID {experience_id} не найден")
            return experience
        
        return self._execute_in_transaction(_get_experience)
    
    def find_experiences(self, 
                        experience_type: Optional[str] = None, 
                        information_category: Optional[str] = None,
                        context_id: Optional[int] = None,
                        source_id: Optional[int] = None,
                        limit: int = 50,
                        offset: int = 0) -> List[Experience]:
        """
        Поиск опыта по различным критериям.
        
        Args:
            experience_type: Фильтр по типу опыта
            information_category: Фильтр по категории информации
            context_id: Фильтр по контексту
            source_id: Фильтр по источнику
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            List[Experience]: Список найденных объектов опыта
        """
        def _find_experiences(session: Session) -> List[Experience]:
            query = session.query(Experience)
            
            if experience_type:
                query = query.filter(Experience.experience_type == experience_type)
                
            if information_category:
                query = query.filter(Experience.information_category == information_category)
                
            if context_id:
                query = query.filter(Experience.context_id == context_id)
                
            if source_id:
                query = query.filter(Experience.source_id == source_id)
            
            # Сортировка по времени создания от новых к старым
            query = query.order_by(Experience.timestamp.desc())
            
            # Применяем пагинацию
            query = query.limit(limit).offset(offset)
            
            return query.all()
        
        return self._execute_in_transaction(_find_experiences)
    
    def find_similar_experiences(self, 
                               content: str,
                               min_similarity: float = 0.7,
                               limit: int = 5) -> List[Tuple[Experience, float]]:
        """
        Поиск похожих опытов по содержанию с использованием семантического сравнения.
        
        Args:
            content: Текст для поиска похожего опыта
            min_similarity: Минимальная степень сходства (от 0 до 1)
            limit: Максимальное количество результатов
            
        Returns:
            List[Tuple[Experience, float]]: Список пар (опыт, степень сходства)
        """
        try:
            content_vector = vectorize_text(content)
        except Exception as e:
            logger.error(f"Ошибка векторизации текста: {e}")
            return []
        
        def _find_similar(session: Session) -> List[Tuple[Experience, float]]:
            # Используем cosine_similarity для поиска похожих векторов
            # Здесь нужно использовать сырой SQL запрос с вызовом функции pgvector
            # TODO: Реализовать семантический поиск через pgvector
            
            # Упрощенная заглушка для демонстрации
            # В реальном коде здесь должен быть запрос к pgvector с использованием cosine_similarity
            results = []
            experiences = session.query(Experience).filter(Experience.content_vector.is_not(None)).limit(100).all()
            
            for exp in experiences:
                # Здесь должно быть сравнение векторов через pgvector
                # В заглушке просто возвращаем первые несколько записей
                similarity = 0.8  # Заглушка для similarity
                if similarity >= min_similarity:
                    results.append((exp, similarity))
            
            # Сортируем по убыванию сходства и ограничиваем количество
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        
        return self._execute_in_transaction(_find_similar)
    
    # === Методы для работы со связями ===
    
    def create_connection(self,
                         source_experience_id: int,
                         target_experience_id: int,
                         connection_type: str,
                         strength: int = 5,
                         bidirectional: bool = False,
                         description: Optional[str] = None) -> ExperienceConnection:
        """
        Создание связи между опытами.
        
        Args:
            source_experience_id: ID исходного опыта
            target_experience_id: ID целевого опыта
            connection_type: Тип связи (TYPE_TEMPORAL, TYPE_CAUSAL и т.д.)
            strength: Сила связи от 1 до 10
            bidirectional: Флаг двунаправленной связи
            description: Описание связи
            
        Returns:
            ExperienceConnection: Созданный объект связи
            
        Raises:
            ExperienceNotFoundError: Если один из опытов не найден
            AssociationError: При ошибке создания связи
        """
        def _create_connection(session: Session) -> ExperienceConnection:
            # Проверяем существование обоих опытов
            source = session.query(Experience).filter(Experience.id == source_experience_id).first()
            if not source:
                raise ExperienceNotFoundError(f"Исходный опыт с ID {source_experience_id} не найден")
                
            target = session.query(Experience).filter(Experience.id == target_experience_id).first()
            if not target:
                raise ExperienceNotFoundError(f"Целевой опыт с ID {target_experience_id} не найден")
            
            # Проверяем, не существует ли уже такая связь
            existing = session.query(ExperienceConnection).filter(
                ExperienceConnection.source_experience_id == source_experience_id,
                ExperienceConnection.target_experience_id == target_experience_id
            ).first()
            
            if existing:
                # Если связь уже есть, просто обновляем её параметры
                existing.connection_type = connection_type
                existing.strength = strength
                existing.direction = (ExperienceConnection.DIRECTION_BI if bidirectional 
                                     else ExperienceConnection.DIRECTION_UNI)
                existing.description = description
                existing.last_activated = datetime.now()
                existing.activation_count += 1
                return existing
                
            # Создаем новую связь
            direction = (ExperienceConnection.DIRECTION_BI if bidirectional 
                         else ExperienceConnection.DIRECTION_UNI)
            
            connection = ExperienceConnection(
                source_experience_id=source_experience_id,
                target_experience_id=target_experience_id,
                connection_type=connection_type,
                strength=strength,
                direction=direction,
                description=description
            )
            
            session.add(connection)
            session.flush()
            
            return connection
        
        return self._execute_in_transaction(_create_connection)
    
    def find_connected_experiences(self, 
                                 experience_id: int,
                                 connection_types: Optional[List[str]] = None,
                                 min_strength: int = 1,
                                 max_results: int = 20) -> List[Tuple[Experience, ExperienceConnection]]:
        """
        Поиск опытов, связанных с указанным.
        
        Args:
            experience_id: ID опыта для поиска связей
            connection_types: Список типов связей для фильтрации
            min_strength: Минимальная сила связи
            max_results: Максимальное количество результатов
            
        Returns:
            List[Tuple[Experience, ExperienceConnection]]: Список пар (связанный опыт, связь)
        """
        def _find_connected(session: Session) -> List[Tuple[Experience, ExperienceConnection]]:
            # Запрос исходящих связей
            outgoing_query = (
                session.query(Experience, ExperienceConnection)
                .join(ExperienceConnection, ExperienceConnection.target_experience_id == Experience.id)
                .filter(ExperienceConnection.source_experience_id == experience_id)
                .filter(ExperienceConnection.strength >= min_strength)
            )
            
            # Запрос входящих связей
            incoming_query = (
                session.query(Experience, ExperienceConnection)
                .join(ExperienceConnection, ExperienceConnection.source_experience_id == Experience.id)
                .filter(ExperienceConnection.target_experience_id == experience_id)
                .filter(ExperienceConnection.strength >= min_strength)
            )
            
            # Применяем фильтр по типам связей
            if connection_types:
                outgoing_query = outgoing_query.filter(
                    ExperienceConnection.connection_type.in_(connection_types)
                )
                incoming_query = incoming_query.filter(
                    ExperienceConnection.connection_type.in_(connection_types)
                )
            
            # Объединяем результаты
            results = list(outgoing_query.all())
            results.extend(incoming_query.all())
            
            # Сортируем по силе связи (от сильных к слабым)
            results.sort(key=lambda x: x[1].strength, reverse=True)
            
            return results[:max_results]
        
        return self._execute_in_transaction(_find_connected)
    
    # === Методы для работы с контекстами и источниками ===
    
    def get_or_create_source(self, 
                           name: str, 
                           source_type: str, 
                           information_category: str,
                           **kwargs) -> ExperienceSource:
        """
        Получение или создание источника опыта.
        
        Args:
            name: Имя источника
            source_type: Тип источника (SOURCE_TYPE_HUMAN, SOURCE_TYPE_AMI и т.д.)
            information_category: Категория информации (CATEGORY_SELF, CATEGORY_SUBJECT и т.д.)
            **kwargs: Дополнительные параметры для создания источника
            
        Returns:
            ExperienceSource: Объект источника опыта
        """
        def _get_or_create_source(session: Session) -> ExperienceSource:
            # Пытаемся найти существующий источник
            source = session.query(ExperienceSource).filter(
                ExperienceSource.name == name,
                ExperienceSource.source_type == source_type
            ).first()
            
            if source:
                # Обновляем время последнего взаимодействия и счетчик
                source.last_interaction = datetime.now()
                source.interaction_count += 1
                return source
            
            # Создаем новый источник
            source = ExperienceSource(
                name=name,
                source_type=source_type,
                information_category=information_category,
                **kwargs
            )
            
            session.add(source)
            session.flush()
            
            return source
        
        return self._execute_in_transaction(_get_or_create_source)
    
    def activate_context(self, context_id: int) -> ExperienceContext:
        """
        Активация контекста.
        
        Args:
            context_id: ID контекста для активации
            
        Returns:
            ExperienceContext: Активированный контекст
            
        Raises:
            ValueError: Если контекст не найден
        """
        def _activate_context(session: Session) -> ExperienceContext:
            context = session.query(ExperienceContext).filter(
                ExperienceContext.id == context_id
            ).first()
            
            if not context:
                raise ValueError(f"Контекст с ID {context_id} не найден")
                
            # Если контекст уже активен, просто возвращаем его
            if context.active_status:
                return context
                
            # Активируем контекст
            context.active_status = True
            
            return context
        
        return self._execute_in_transaction(_activate_context)
    
    # === Вспомогательные методы ===
    
    def add_attributes_to_experience(self, 
                                   experience_id: int, 
                                   attributes: Dict[str, Any]) -> List[ExperienceAttribute]:
        """
        Добавление атрибутов к опыту.
        
        Args:
            experience_id: ID опыта
            attributes: Словарь атрибутов для добавления
            
        Returns:
            List[ExperienceAttribute]: Список созданных атрибутов
            
        Raises:
            ExperienceNotFoundError: Если опыт не найден
        """
        def _add_attributes(session: Session) -> List[ExperienceAttribute]:
            # Проверяем существование опыта
            experience = session.query(Experience).filter(Experience.id == experience_id).first()
            if not experience:
                raise ExperienceNotFoundError(f"Опыт с ID {experience_id} не найден")
            
            result = []
            for key, value in attributes.items():
                # Проверяем, существует ли уже такой атрибут
                existing = session.query(ExperienceAttribute).filter(
                    ExperienceAttribute.experience_id == experience_id,
                    ExperienceAttribute.attribute_key == key
                ).first()
                
                if existing:
                    # Обновляем существующий атрибут
                    existing.attribute_value = str(value)
                    result.append(existing)
                else:
                    # Создаем новый атрибут
                    attribute = ExperienceAttribute(
                        experience_id=experience_id,
                        attribute_key=key,
                        attribute_value=str(value)
                    )
                    session.add(attribute)
                    result.append(attribute)
            
            return result
        
        return self._execute_in_transaction(_add_attributes)
    
    def update_experience(self, 
                        experience_id: int, 
                        **kwargs) -> Experience:
        """
        Обновление полей опыта.
        
        Args:
            experience_id: ID опыта для обновления
            **kwargs: Поля для обновления
            
        Returns:
            Experience: Обновленный объект опыта
            
        Raises:
            ExperienceNotFoundError: Если опыт не найден
        """
        def _update_experience(session: Session) -> Experience:
            experience = session.query(Experience).filter(Experience.id == experience_id).first()
            if not experience:
                raise ExperienceNotFoundError(f"Опыт с ID {experience_id} не найден")
            
            # Обновляем поля
            for key, value in kwargs.items():
                if hasattr(experience, key):
                    setattr(experience, key, value)
            
            return experience
        
        return self._execute_in_transaction(_update_experience)