"""
Тесты для утилит работы с векторами.

Проверяет работу класса VectorEncoder и вспомогательных функций
для преобразования текста в векторные представления и их сравнения.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from ...utils.vector_utils import VectorEncoder, batch_encode_texts, find_most_similar


class TestVectorEncoder:
    """Тесты для класса VectorEncoder."""
    
    def test_init_with_default_model(self):
        """Проверяет инициализацию энкодера с моделью по умолчанию."""
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            encoder = VectorEncoder()
            mock_transformer.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")
            assert encoder.model == mock_transformer.return_value
    
    def test_init_with_custom_model(self):
        """Проверяет инициализацию энкодера с пользовательской моделью."""
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            encoder = VectorEncoder(model_name="custom-model")
            mock_transformer.assert_called_once_with("custom-model")
            assert encoder.model == mock_transformer.return_value
    
    def test_init_handles_import_error(self):
        """Проверяет, что энкодер корректно обрабатывает отсутствие sentence_transformers."""
        with patch('sentence_transformers.SentenceTransformer', side_effect=ImportError):
            with pytest.raises(ImportError) as exc_info:
                VectorEncoder()
            assert "sentence-transformers" in str(exc_info.value)
            assert "pip install" in str(exc_info.value)
    
    def test_encode_single_text(self):
        """Проверяет кодирование одного текста."""
        # Создаем мок для модели
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            encoder = VectorEncoder()
            result = encoder.encode("test text")
            
            # Проверяем, что модель была вызвана с правильными параметрами
            mock_model.encode.assert_called_once_with("test text", normalize_embeddings=True)
            
            # Проверяем, что результат корректный
            assert isinstance(result, np.ndarray)
            assert np.array_equal(result, np.array([0.1, 0.2, 0.3]))
    
    def test_encode_multiple_texts(self):
        """Проверяет кодирование списка текстов."""
        # Создаем мок для модели
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            encoder = VectorEncoder()
            result = encoder.encode(["text1", "text2"])
            
            # Проверяем, что модель была вызвана с правильными параметрами
            mock_model.encode.assert_called_once_with(["text1", "text2"], normalize_embeddings=True)
            
            # Проверяем, что результат корректный
            assert isinstance(result, np.ndarray)
            assert result.shape == (2, 2)  # 2 текста, 2 размерности
    
    def test_compute_similarity(self):
        """Проверяет вычисление сходства между двумя текстами."""
        # Создаем мок для модели
        mock_model = MagicMock()
        # Модель возвращает два разных вектора при кодировании
        mock_model.encode.side_effect = [
            np.array([0.1, 0.2]),  # для первого текста
            np.array([0.2, 0.3])   # для второго текста
        ]
        
        # Создаем мок для cos_sim
        mock_cos_sim = np.array([[0.95]])  # высокое сходство
        
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            with patch('sentence_transformers.util.cos_sim', return_value=mock_cos_sim):
                encoder = VectorEncoder()
                similarity = encoder.compute_similarity("text1", "text2")
                
                # Проверяем, что вызывалась функция сходства
                assert similarity == 0.95


def test_batch_encode_texts():
    """Проверяет пакетное кодирование текстов."""
    # Создаем мок для энкодера
    mock_encoder = MagicMock()
    mock_encoder.encode.side_effect = [
        [np.array([0.1, 0.2]), np.array([0.3, 0.4])],  # первый батч
        [np.array([0.5, 0.6])]                         # второй батч
    ]
    
    # Тестовые тексты
    texts = ["text1", "text2", "text3"]
    
    # Вызываем функцию с размером батча 2
    result = batch_encode_texts(mock_encoder, texts, batch_size=2)
    
    # Проверяем, что энкодер был вызван дважды с правильными текстами
    assert mock_encoder.encode.call_count == 2
    mock_encoder.encode.assert_any_call(["text1", "text2"])
    mock_encoder.encode.assert_any_call(["text3"])
    
    # Проверяем, что результат включает все три вектора
    assert len(result) == 3


def test_find_most_similar():
    """Проверяет нахождение наиболее похожих векторов."""
    # Создаем тестовый запрос и векторы
    query_vector = np.array([1.0, 0.0])
    vectors = [
        np.array([0.9, 0.1]),   # сходство 0.9
        np.array([0.5, 0.5]),   # сходство 0.5
        np.array([0.1, 0.9])    # сходство 0.1
    ]
    
    # Результаты сходства
    similarities = [
        np.array([[0.9]]),
        np.array([[0.5]]),
        np.array([[0.1]])
    ]
    
    # Патчим функцию cos_sim для возврата предопределенных значений
    with patch('sentence_transformers.util.cos_sim', side_effect=similarities):
        # Находим 2 наиболее похожих вектора
        result = find_most_similar(query_vector, vectors, top_n=2)
        
        # Проверяем результат - должны быть индексы 0 и 1 (в порядке убывания сходства)
        assert len(result) == 2
        assert result[0][0] == 0  # индекс первого вектора
        assert result[0][1] == 0.9  # его сходство
        assert result[1][0] == 1  # индекс второго вектора
        assert result[1][1] == 0.5  # его сходство