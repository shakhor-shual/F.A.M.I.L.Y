"""
Утилиты для работы с векторами.

Модуль предоставляет класс VectorEncoder для преобразования текста в векторы
с помощью моделей Sentence Transformers, а также вспомогательные функции
для обработки и сравнения векторов.
"""

import numpy as np
from typing import List, Union, Optional


class VectorEncoder:
    """
    Класс для кодирования текста в векторные представления.
    
    Использует модели Sentence Transformers для создания векторных эмбеддингов.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Инициализирует энкодер с указанной моделью.
        
        Args:
            model_name (str): Идентификатор предобученной модели Sentence Transformers
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError(
                "Для работы VectorEncoder требуется sentence-transformers. "
                "Установите его с помощью 'pip install sentence-transformers'"
            )
    
    def encode(self, text: Union[str, List[str]], normalize: bool = True) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Кодирует текст или список текстов в векторы.
        
        Args:
            text (Union[str, List[str]]): Текст или список текстов для кодирования
            normalize (bool): Нормализовать ли векторы (по умолчанию True)
            
        Returns:
            Union[np.ndarray, List[np.ndarray]]: Векторное представление текста или список векторов
        """
        embeddings = self.model.encode(text, normalize_embeddings=normalize)
        return embeddings
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Вычисляет косинусное сходство между двумя текстами.
        
        Args:
            text1 (str): Первый текст
            text2 (str): Второй текст
            
        Returns:
            float: Косинусное сходство (от 0 до 1, где 1 - идентичные тексты)
        """
        from sentence_transformers.util import cos_sim
        embedding1 = self.encode(text1).reshape(1, -1)
        embedding2 = self.encode(text2).reshape(1, -1)
        return float(cos_sim(embedding1, embedding2)[0][0])


def batch_encode_texts(encoder: VectorEncoder, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
    """
    Кодирует список текстов с использованием батчей для оптимизации памяти и скорости.
    
    Args:
        encoder (VectorEncoder): Инициализированный энкодер
        texts (List[str]): Список текстов для кодирования
        batch_size (int): Размер батча
        
    Returns:
        List[np.ndarray]: Список векторных представлений
    """
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_vectors = encoder.encode(batch)
        vectors.extend(batch_vectors)
    return vectors


def find_most_similar(query_vector: np.ndarray, vectors: List[np.ndarray], top_n: int = 5) -> List[tuple]:
    """
    Находит наиболее похожие векторы из списка.
    
    Args:
        query_vector (np.ndarray): Запрос в виде вектора
        vectors (List[np.ndarray]): Список векторов для сравнения
        top_n (int): Количество наиболее похожих векторов для возврата
        
    Returns:
        List[tuple]: Список кортежей (индекс, сходство) упорядоченных по убыванию сходства
    """
    from sentence_transformers.util import cos_sim
    similarities = []
    query_vector = query_vector.reshape(1, -1)
    
    for i, vector in enumerate(vectors):
        vector = vector.reshape(1, -1)
        similarity = float(cos_sim(query_vector, vector)[0][0])
        similarities.append((i, similarity))
    
    # Сортировка по убыванию сходства
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем top_n наиболее похожих
    return similarities[:top_n]