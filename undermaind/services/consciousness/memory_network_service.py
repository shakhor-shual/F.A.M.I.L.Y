"""
Сервис управления сетью памяти АМИ (MemoryNetworkService).

Этот модуль реализует управление сетью связей между опытами АМИ,
обеспечивая структурную организацию памяти, формирование ассоциаций
и навигацию по сети связей.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple, Union, Set
from datetime import datetime
from sqlalchemy import func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from undermaind.models.consciousness.experience import Experience
from undermaind.models.consciousness.experience_connection import ExperienceConnection
from undermaind.models.consciousness.experience_contexts import ExperienceContext
from undermaind.services.base import BaseService
from undermaind.core.session import SessionManager
from undermaind.utils.vector_utils import cosine_similarity, vectorize_text

logger = logging.getLogger(__name__)


class NetworkAnalysisError(Exception):
    """Исключение, вызываемое при ошибке анализа сети связей."""
    pass


class ConnectionNotFoundError(Exception):
    """Исключение, вызываемое когда связь не найдена."""
    pass


class MemoryNetworkService(BaseService):
    """
    Сервис для управления сетью связей между опытами АМИ.
    
    Этот сервис отвечает за структурную организацию памяти,
    создание и укрепление связей, навигацию и анализ сети воспоминаний.
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Инициализация сервиса управления сетью памяти.
        
        Args:
            session_manager: Менеджер сессий для работы с БД
        """
        super().__init__(session_manager)
    
    # === Методы управления связями ===
    
    def create_connection(self,
                         source_id: int,
                         target_id: int,
                         connection_type: str,
                         bidirectional: bool = False,
                         strength: int = 5,
                         conscious_status: bool = True,
                         description: Optional[str] = None,
                         meta_data: Optional[Dict[str, Any]] = None) -> ExperienceConnection:
        """
        Создание новой связи между опытами.
        
        Args:
            source_id: ID исходного опыта
            target_id: ID целевого опыта
            connection_type: Тип связи (TYPE_TEMPORAL, TYPE_CAUSAL и т.д.)
            bidirectional: Создавать ли двунаправленную связь
            strength: Сила связи от 1 до 10
            conscious_status: Осознаваемая ли связь
            description: Описание связи
            meta_data: Дополнительные метаданные
            
        Returns:
            ExperienceConnection: Созданный объект связи
            
        Raises:
            ValueError: Если один из опытов не найден
            SQLAlchemyError: При ошибке БД
        """
        def _create_connection(session: Session) -> ExperienceConnection:
            # Проверяем существование опытов
            source = session.query(Experience).filter(Experience.id == source_id).first()
            if source is None:
                raise ValueError(f"Опыт с ID {source_id} не найден")
                
            target = session.query(Experience).filter(Experience.id == target_id).first()
            if target is None:
                raise ValueError(f"Опыт с ID {target_id} не найден")
            
            # Проверяем, не существует ли уже такая связь
            existing = session.query(ExperienceConnection).filter(
                ExperienceConnection.source_experience_id == source_id,
                ExperienceConnection.target_experience_id == target_id,
                ExperienceConnection.connection_type == connection_type
            ).first()
            
            if existing:
                # Если связь уже существует, обновляем её
                existing.strength = strength
                existing.direction = ExperienceConnection.DIRECTION_BI if bidirectional else ExperienceConnection.DIRECTION_UNI
                existing.conscious_status = conscious_status
                existing.description = description if description else existing.description
                existing.last_activated = datetime.now()
                existing.activation_count += 1
                
                # Обновляем метаданные, если они переданы
                if meta_data:
                    if not existing.meta_data:
                        existing.meta_data = {}
                    existing.meta_data.update(meta_data)
                
                return existing
            
            # Создаем новую связь
            direction = ExperienceConnection.DIRECTION_BI if bidirectional else ExperienceConnection.DIRECTION_UNI
            connection = ExperienceConnection(
                source_experience_id=source_id,
                target_experience_id=target_id,
                connection_type=connection_type,
                strength=strength,
                direction=direction,
                conscious_status=conscious_status,
                description=description,
                meta_data=meta_data or {}
            )
            
            session.add(connection)
            session.flush()  # Для получения ID
            
            return connection
            
        return self._execute_in_transaction(_create_connection)
    
    def get_connection(self, connection_id: int) -> ExperienceConnection:
        """
        Получение связи по ID.
        
        Args:
            connection_id: ID связи
            
        Returns:
            ExperienceConnection: Объект связи
            
        Raises:
            ConnectionNotFoundError: Если связь не найдена
        """
        def _get_connection(session: Session) -> ExperienceConnection:
            connection = session.query(ExperienceConnection).filter(
                ExperienceConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ConnectionNotFoundError(f"Связь с ID {connection_id} не найдена")
                
            return connection
            
        return self._execute_in_transaction(_get_connection)
    
    def update_connection_strength(self, connection_id: int, new_strength: int) -> ExperienceConnection:
        """
        Обновление силы связи между опытами.
        
        Args:
            connection_id: ID связи
            new_strength: Новая сила связи от 1 до 10
            
        Returns:
            ExperienceConnection: Обновленный объект связи
            
        Raises:
            ConnectionNotFoundError: Если связь не найдена
            ValueError: Если значение силы связи некорректно
        """
        # Проверяем валидность значения
        if not 1 <= new_strength <= 10:
            raise ValueError("Сила связи должна быть от 1 до 10")
            
        def _update_strength(session: Session) -> ExperienceConnection:
            connection = session.query(ExperienceConnection).filter(
                ExperienceConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ConnectionNotFoundError(f"Связь с ID {connection_id} не найдена")
                
            connection.strength = new_strength
            connection.last_activated = datetime.now()
            connection.activation_count += 1
            
            return connection
            
        return self._execute_in_transaction(_update_strength)
    
    def activate_connection(self, connection_id: int) -> ExperienceConnection:
        """
        Активация существующей связи (увеличение счетчика активаций).
        
        Args:
            connection_id: ID связи
            
        Returns:
            ExperienceConnection: Обновленный объект связи
        """
        def _activate(session: Session) -> ExperienceConnection:
            connection = session.query(ExperienceConnection).filter(
                ExperienceConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ConnectionNotFoundError(f"Связь с ID {connection_id} не найдена")
                
            connection.last_activated = datetime.now()
            connection.activation_count += 1
            
            return connection
            
        return self._execute_in_transaction(_activate)
    
    # === Методы поиска и навигации по связям ===
    
    def find_connected_experiences(self, 
                                  experience_id: int,
                                  connection_types: Optional[List[str]] = None,
                                  min_strength: int = 1,
                                  only_conscious: bool = False,
                                  limit: int = 20) -> List[Tuple[Experience, ExperienceConnection]]:
        """
        Поиск опытов, связанных с указанным.
        
        Args:
            experience_id: ID опыта для поиска связей
            connection_types: Список типов связей для фильтрации
            min_strength: Минимальная сила связи
            only_conscious: Фильтровать только осознаваемые связи
            limit: Максимальное количество результатов
            
        Returns:
            List[Tuple[Experience, ExperienceConnection]]: Список пар (опыт, связь)
        """
        def _find_connected(session: Session) -> List[Tuple[Experience, ExperienceConnection]]:
            # Базовые запросы
            outgoing_query = (
                session.query(Experience, ExperienceConnection)
                .join(ExperienceConnection, ExperienceConnection.target_experience_id == Experience.id)
                .filter(
                    ExperienceConnection.source_experience_id == experience_id,
                    ExperienceConnection.strength >= min_strength
                )
            )
            
            incoming_query = (
                session.query(Experience, ExperienceConnection)
                .join(ExperienceConnection, ExperienceConnection.source_experience_id == Experience.id)
                .filter(
                    ExperienceConnection.target_experience_id == experience_id,
                    ExperienceConnection.strength >= min_strength
                )
            )
            
            # Дополнительные фильтры
            if connection_types:
                outgoing_query = outgoing_query.filter(
                    ExperienceConnection.connection_type.in_(connection_types)
                )
                incoming_query = incoming_query.filter(
                    ExperienceConnection.connection_type.in_(connection_types)
                )
                
            if only_conscious:
                outgoing_query = outgoing_query.filter(ExperienceConnection.conscious_status == True)
                incoming_query = incoming_query.filter(ExperienceConnection.conscious_status == True)
            
            # Объединяем результаты
            results = list(outgoing_query.all())
            results.extend(list(incoming_query.all()))
            
            # Сортируем по силе связи и активности
            results.sort(key=lambda x: (x[1].strength, x[1].activation_count), reverse=True)
            
            return results[:limit]
            
        return self._execute_in_transaction(_find_connected)
    
    def find_path_between_experiences(self, 
                                     start_id: int, 
                                     end_id: int, 
                                     max_depth: int = 4,
                                     min_strength: int = 3) -> List[List[Tuple[Experience, ExperienceConnection]]]:
        """
        Поиск путей между двумя опытами в сети связей.
        
        Args:
            start_id: ID начального опыта
            end_id: ID конечного опыта
            max_depth: Максимальная глубина поиска
            min_strength: Минимальная сила связей для поиска
            
        Returns:
            List[List[Tuple[Experience, ExperienceConnection]]]: Список найденных путей
            
        Raises:
            ValueError: Если один из опытов не найден
            NetworkAnalysisError: При других ошибках анализа сети
        """
        def _find_paths(session: Session) -> List[List[Tuple[Experience, ExperienceConnection]]]:
            # Проверяем существование опытов
            if not session.query(Experience).filter(Experience.id == start_id).first():
                raise ValueError(f"Начальный опыт с ID {start_id} не найден")
                
            if not session.query(Experience).filter(Experience.id == end_id).first():
                raise ValueError(f"Конечный опыт с ID {end_id} не найден")
            
            # Реализация поиска путей в глубину
            paths = []
            visited = set()
            current_path = []
            
            def dfs(current_id, depth=0):
                if depth > max_depth:
                    return
                    
                if current_id == end_id:
                    # Нашли путь, сохраняем его копию
                    paths.append(list(current_path))
                    return
                    
                if current_id in visited:
                    return
                    
                visited.add(current_id)
                
                # Получаем все исходящие связи
                connections = session.query(ExperienceConnection, Experience).filter(
                    ExperienceConnection.source_experience_id == current_id,
                    ExperienceConnection.strength >= min_strength
                ).join(
                    Experience, 
                    ExperienceConnection.target_experience_id == Experience.id
                ).all()
                
                for conn, exp in connections:
                    if exp.id not in visited:
                        current_path.append((exp, conn))
                        dfs(exp.id, depth + 1)
                        current_path.pop()  # Возвращаемся назад
                
                # Получаем все входящие связи от двунаправленных связей
                connections = session.query(ExperienceConnection, Experience).filter(
                    ExperienceConnection.target_experience_id == current_id,
                    ExperienceConnection.strength >= min_strength,
                    ExperienceConnection.direction == ExperienceConnection.DIRECTION_BI
                ).join(
                    Experience, 
                    ExperienceConnection.source_experience_id == Experience.id
                ).all()
                
                for conn, exp in connections:
                    if exp.id not in visited:
                        current_path.append((exp, conn))
                        dfs(exp.id, depth + 1)
                        current_path.pop()  # Возвращаемся назад
                        
                visited.remove(current_id)
            
            # Начинаем поиск с начального опыта
            start_exp = session.query(Experience).filter(Experience.id == start_id).first()
            dfs(start_id)
            
            return paths
            
        return self._execute_in_transaction(_find_paths)
    
    def find_experiences_by_context_proximity(self,
                                            experience_id: int,
                                            max_distance: int = 2,
                                            limit: int = 10) -> List[Experience]:
        """
        Поиск опытов близких по контексту к указанному.
        
        Args:
            experience_id: ID опыта для поиска близких по контексту
            max_distance: Максимальное расстояние в дереве контекстов
            limit: Максимальное количество результатов
            
        Returns:
            List[Experience]: Список найденных опытов
        """
        def _find_by_context(session: Session) -> List[Experience]:
            # Получаем исходный опыт и его контекст
            experience = session.query(Experience).filter(Experience.id == experience_id).first()
            
            if not experience:
                raise ValueError(f"Опыт с ID {experience_id} не найден")
            
            if not experience.context_id:
                return []  # Если у опыта нет контекста, возвращаем пустой список
                
            # Получаем все ID контекстов в пределах max_distance
            context_ids = [experience.context_id]
            
            # Получаем родительские контексты
            current_context_id = experience.context_id
            distance = 0
            
            while distance < max_distance:
                parent = session.query(ExperienceContext.parent_context_id).filter(
                    ExperienceContext.id == current_context_id
                ).first()
                
                if not parent or not parent[0]:
                    break
                    
                context_ids.append(parent[0])
                current_context_id = parent[0]
                distance += 1
            
            # Получаем дочерние контексты
            to_process = [experience.context_id]
            processed = set([experience.context_id])
            depth = 0
            
            while to_process and depth < max_distance:
                next_level = []
                
                for ctx_id in to_process:
                    children = session.query(ExperienceContext.id).filter(
                        ExperienceContext.parent_context_id == ctx_id
                    ).all()
                    
                    for child in children:
                        if child[0] not in processed:
                            context_ids.append(child[0])
                            next_level.append(child[0])
                            processed.add(child[0])
                
                to_process = next_level
                depth += 1
            
            # Находим опыты из этих контекстов, исключая исходный опыт
            results = session.query(Experience).filter(
                Experience.context_id.in_(context_ids),
                Experience.id != experience_id
            ).order_by(
                desc(Experience.salience),  # Сначала наиболее значимые опыты
                desc(Experience.timestamp)  # Затем по времени
            ).limit(limit).all()
            
            return results
            
        return self._execute_in_transaction(_find_by_context)
    
    # === Методы анализа сети связей ===
    
    def calculate_experience_centrality(self, experience_id: int) -> Dict[str, float]:
        """
        Расчет центральности опыта в сети связей.
        
        Центральность определяет важность узла (опыта) в сети связей
        и может быть выражена различными метриками.
        
        Args:
            experience_id: ID опыта для анализа
            
        Returns:
            Dict[str, float]: Словарь метрик центральности
            
        Raises:
            ValueError: Если опыт не найден
        """
        def _calculate_centrality(session: Session) -> Dict[str, float]:
            # Проверяем существование опыта
            if not session.query(Experience).filter(Experience.id == experience_id).first():
                raise ValueError(f"Опыт с ID {experience_id} не найден")
                
            # Считаем количество входящих связей
            incoming_count = session.query(func.count(ExperienceConnection.id)).filter(
                ExperienceConnection.target_experience_id == experience_id
            ).scalar() or 0
            
            # Считаем количество исходящих связей
            outgoing_count = session.query(func.count(ExperienceConnection.id)).filter(
                ExperienceConnection.source_experience_id == experience_id
            ).scalar() or 0
            
            # Считаем общее количество связей
            total_connections = incoming_count + outgoing_count
            
            # Среднюю силу входящих связей
            avg_incoming_strength = (
                session.query(func.avg(ExperienceConnection.strength))
                .filter(ExperienceConnection.target_experience_id == experience_id)
                .scalar() or 0
            )
            
            # Среднюю силу исходящих связей
            avg_outgoing_strength = (
                session.query(func.avg(ExperienceConnection.strength))
                .filter(ExperienceConnection.source_experience_id == experience_id)
                .scalar() or 0
            )
            
            # Формируем результат
            result = {
                "degree_centrality": total_connections,
                "in_degree": incoming_count,
                "out_degree": outgoing_count,
                "avg_incoming_strength": float(avg_incoming_strength),
                "avg_outgoing_strength": float(avg_outgoing_strength),
                "weighted_centrality": (float(avg_incoming_strength) * incoming_count + 
                                      float(avg_outgoing_strength) * outgoing_count)
            }
            
            return result
            
        return self._execute_in_transaction(_calculate_centrality)
    
    def suggest_new_connections(self, 
                              experience_id: int, 
                              min_similarity: float = 0.7,
                              max_suggestions: int = 5) -> List[Tuple[int, str, float]]:
        """
        Предложение новых связей для опыта на основе существующей сети.
        
        Args:
            experience_id: ID опыта для анализа
            min_similarity: Минимальный порог схожести для предложений
            max_suggestions: Максимальное количество предложений
            
        Returns:
            List[Tuple[int, str, float]]: Список предложений (ID опыта, тип связи, сила)
        """
        def _suggest_connections(session: Session) -> List[Tuple[int, str, float]]:
            # Получаем исходный опыт
            experience = session.query(Experience).filter(Experience.id == experience_id).first()
            
            if not experience:
                raise ValueError(f"Опыт с ID {experience_id} не найден")
            
            # Получаем все существующие связи опыта
            existing_connections = set()
            
            outgoing = session.query(ExperienceConnection.target_experience_id).filter(
                ExperienceConnection.source_experience_id == experience_id
            ).all()
            
            incoming = session.query(ExperienceConnection.source_experience_id).filter(
                ExperienceConnection.target_experience_id == experience_id
            ).all()
            
            for conn in outgoing:
                existing_connections.add(conn[0])
            
            for conn in incoming:
                existing_connections.add(conn[0])
            
            suggestions = []
            
            # Вариант 1: Связи через общие узлы (если A связан с B и B связан с C, то можно предложить связать A и C)
            common_nodes_query = """
            WITH connected_to_source AS (
                -- Опыты, связанные с исходным
                SELECT target_experience_id AS id FROM experience_connections 
                WHERE source_experience_id = :exp_id
                UNION
                SELECT source_experience_id AS id FROM experience_connections 
                WHERE target_experience_id = :exp_id
            ),
            potential_connections AS (
                -- Опыты, связанные с опытами, связанными с исходным
                SELECT 
                    CASE 
                        WHEN ec.source_experience_id IN (SELECT id FROM connected_to_source) 
                        THEN ec.target_experience_id 
                        ELSE ec.source_experience_id 
                    END AS potential_id,
                    ec.connection_type,
                    ec.strength
                FROM experience_connections ec
                WHERE 
                    (ec.source_experience_id IN (SELECT id FROM connected_to_source) OR 
                     ec.target_experience_id IN (SELECT id FROM connected_to_source))
                    AND ec.source_experience_id != :exp_id
                    AND ec.target_experience_id != :exp_id
            )
            SELECT 
                potential_id, 
                connection_type,
                AVG(strength) as avg_strength,
                COUNT(*) as connection_count
            FROM potential_connections
            WHERE potential_id NOT IN (
                -- Исключаем уже связанные с исходным опыты
                SELECT target_experience_id FROM experience_connections WHERE source_experience_id = :exp_id
                UNION
                SELECT source_experience_id FROM experience_connections WHERE target_experience_id = :exp_id
            )
            GROUP BY potential_id, connection_type
            ORDER BY connection_count DESC, avg_strength DESC
            LIMIT :limit
            """
            
            result = session.execute(common_nodes_query, {
                "exp_id": experience_id,
                "limit": max_suggestions * 2  # Берем с запасом для фильтрации
            }).fetchall()
            
            # Преобразуем результаты в предложения
            for row in result:
                target_id, conn_type, avg_strength, _ = row
                
                # Проверяем семантическую близость, если есть векторы
                if experience.content_vector is not None:
                    target_exp = session.query(Experience).filter(Experience.id == target_id).first()
                    if target_exp and target_exp.content_vector is not None:
                        similarity = cosine_similarity(
                            experience.content_vector, target_exp.content_vector
                        )
                        
                        if similarity >= min_similarity:
                            # Предлагаем связь, корректируя силу на основе схожести
                            adjusted_strength = min(10, round(avg_strength * similarity))
                            suggestions.append((target_id, conn_type, similarity))
                else:
                    # Если нет векторов, просто предлагаем на основе сети
                    suggestions.append((target_id, conn_type, float(avg_strength)))
            
            return suggestions[:max_suggestions]
            
        return self._execute_in_isolated_transaction(_suggest_connections)
    
    # === Методы для групповых операций с сетью ===
    
    def strengthen_connections_by_cooccurrence(self, 
                                             context_id: int, 
                                             time_window_seconds: int = 600,
                                             min_strength_increase: float = 0.5) -> int:
        """
        Укрепление связей между опытами, которые появились в одном контексте 
        в близком временном окне.
        
        Args:
            context_id: ID контекста для анализа
            time_window_seconds: Временное окно для совместного появления опытов (в секундах)
            min_strength_increase: Минимальное увеличение силы связи
        
        Returns:
            int: Количество усиленных связей
        """
        def _strengthen_by_cooccurrence(session: Session) -> int:
            # Проверяем существование контекста
            if not session.query(ExperienceContext).filter(ExperienceContext.id == context_id).first():
                raise ValueError(f"Контекст с ID {context_id} не найден")
            
            # Алиасы для различения опытов в самообъединении
            exp1 = aliased(Experience)
            exp2 = aliased(Experience)
            
            # Находим пары опытов, которые появились в близком временном окне
            cooccurrences = session.query(exp1.id, exp2.id).filter(
                exp1.context_id == context_id,
                exp2.context_id == context_id,
                exp1.id < exp2.id,  # Избегаем дубликатов и самообъединения
                func.abs(func.extract('epoch', exp1.timestamp) - 
                        func.extract('epoch', exp2.timestamp)) < time_window_seconds
            ).all()
            
            connections_updated = 0
            
            # Для каждой пары опытов проверяем существующие связи или создаем новые
            for source_id, target_id in cooccurrences:
                # Ищем существующую связь
                conn = session.query(ExperienceConnection).filter(
                    ExperienceConnection.source_experience_id == source_id,
                    ExperienceConnection.target_experience_id == target_id,
                    ExperienceConnection.connection_type == ExperienceConnection.TYPE_TEMPORAL
                ).first()
                
                if conn:
                    # Если связь существует, усиливаем её
                    increase = max(min_strength_increase, 10 - conn.strength) / 2
                    new_strength = min(10, conn.strength + increase)
                    
                    if new_strength > conn.strength:
                        conn.strength = new_strength
                        conn.last_activated = datetime.now()
                        conn.activation_count += 1
                        connections_updated += 1
                else:
                    # Если связи нет, создаем новую с низкой начальной силой
                    conn = ExperienceConnection(
                        source_experience_id=source_id,
                        target_experience_id=target_id,
                        connection_type=ExperienceConnection.TYPE_TEMPORAL,
                        direction=ExperienceConnection.DIRECTION_BI,
                        strength=3,  # Начальная сила для совместного появления
                        conscious_status=False  # Такие связи обычно не осознаются
                    )
                    session.add(conn)
                    connections_updated += 1
            
            return connections_updated
            
        return self._execute_in_isolated_transaction(_strengthen_by_cooccurrence)
    
    def find_clusters_in_network(self, min_connections: int = 3) -> List[List[int]]:
        """
        Поиск кластеров тесно связанных опытов в сети.
        
        Args:
            min_connections: Минимальное количество связей для включения опыта в кластер
            
        Returns:
            List[List[int]]: Список кластеров (каждый кластер - список ID опытов)
        """
        def _find_clusters(session: Session) -> List[List[int]]:
            # Находим опыты с достаточным количеством связей
            connection_counts = {}
            
            # Считаем исходящие связи
            outgoing = session.query(
                ExperienceConnection.source_experience_id,
                func.count(ExperienceConnection.id)
            ).group_by(
                ExperienceConnection.source_experience_id
            ).all()
            
            for exp_id, count in outgoing:
                connection_counts[exp_id] = connection_counts.get(exp_id, 0) + count
            
            # Считаем входящие связи
            incoming = session.query(
                ExperienceConnection.target_experience_id,
                func.count(ExperienceConnection.id)
            ).group_by(
                ExperienceConnection.target_experience_id
            ).all()
            
            for exp_id, count in incoming:
                connection_counts[exp_id] = connection_counts.get(exp_id, 0) + count
            
            # Фильтруем опыты с достаточным количеством связей
            hub_experiences = [exp_id for exp_id, count in connection_counts.items() 
                             if count >= min_connections]
            
            # Строим граф связей для всех выбранных опытов
            graph = {}
            
            for exp_id in hub_experiences:
                graph[exp_id] = set()
            
            # Получаем связи между хабами
            connections = session.query(
                ExperienceConnection.source_experience_id,
                ExperienceConnection.target_experience_id
            ).filter(
                ExperienceConnection.source_experience_id.in_(hub_experiences),
                ExperienceConnection.target_experience_id.in_(hub_experiences)
            ).all()
            
            for source_id, target_id in connections:
                graph[source_id].add(target_id)
                graph[target_id].add(source_id)  # Для двунаправленных связей
            
            # Находим кластеры с использованием поиска в глубину
            visited = set()
            clusters = []
            
            for exp_id in hub_experiences:
                if exp_id not in visited:
                    # Новый кластер
                    cluster = []
                    stack = [exp_id]
                    
                    while stack:
                        current = stack.pop()
                        
                        if current not in visited:
                            visited.add(current)
                            cluster.append(current)
                            
                            for neighbor in graph.get(current, []):
                                if neighbor not in visited:
                                    stack.append(neighbor)
                    
                    if cluster:
                        clusters.append(cluster)
            
            return clusters
            
        return self._execute_in_isolated_transaction(_find_clusters)
    
    # === Вспомогательные методы ===
    
    def get_connection_types_distribution(self) -> Dict[str, int]:
        """
        Получение распределения типов связей в сети.
        
        Returns:
            Dict[str, int]: Словарь типов связей и их количества
        """
        def _get_distribution(session: Session) -> Dict[str, int]:
            result = session.query(
                ExperienceConnection.connection_type,
                func.count(ExperienceConnection.id)
            ).group_by(
                ExperienceConnection.connection_type
            ).all()
            
            return {conn_type: count for conn_type, count in result}
            
        return self._execute_in_transaction(_get_distribution)
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """
        Получение общей статистики по сети связей.
        
        Returns:
            Dict[str, Any]: Словарь с основными метриками сети
        """
        def _get_statistics(session: Session) -> Dict[str, Any]:
            # Общее количество связей
            total_connections = session.query(func.count(ExperienceConnection.id)).scalar() or 0
            
            # Количество опытов с связями
            experiences_with_connections = session.query(func.count(func.distinct(
                func.coalesce(ExperienceConnection.source_experience_id, 
                            ExperienceConnection.target_experience_id)
            ))).scalar() or 0
            
            # Общее количество опытов
            total_experiences = session.query(func.count(Experience.id)).scalar() or 0
            
            # Средняя сила связи
            avg_strength = (
                session.query(func.avg(ExperienceConnection.strength)).scalar() or 0
            )
            
            # Распределение по типам связей
            connection_types = self.get_connection_types_distribution()
            
            # Средняя степень узла (среднее количество связей на опыт)
            avg_degree = total_connections / max(experiences_with_connections, 1)
            
            # Доля опытов, включенных в сеть
            network_coverage = experiences_with_connections / max(total_experiences, 1)
            
            return {
                "total_connections": total_connections,
                "experiences_with_connections": experiences_with_connections,
                "total_experiences": total_experiences,
                "avg_strength": float(avg_strength),
                "avg_degree": avg_degree,
                "network_coverage": network_coverage,
                "connection_types_distribution": connection_types
            }
            
        return self._execute_in_transaction(_get_statistics)