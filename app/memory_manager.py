# app/memory_manager.py
import os
from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

VECTOR_STORE_PATH = "_vector_store"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class MemoryManager:
    """
    Управляет долговременной памятью Нокса с помощью LangChain,
    векторной базы данных FAISS и модели эмбеддингов.
    """
    def __init__(self):
        print("MemoryManager: Инициализация...")
        
        os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

        model_kwargs = {'device': 'cpu'}
        
        print(f"MemoryManager: Загрузка модели эмбеддингов '{EMBEDDING_MODEL_NAME}' на CPU...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs=model_kwargs
        )
        print("MemoryManager: Модель эмбеддингов успешно загружена.")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

        if self._is_store_initialized():
            print(f"MemoryManager: Загрузка существующей векторной базы из '{VECTOR_STORE_PATH}'...")
            self.vector_store = FAISS.load_local(VECTOR_STORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
            print("MemoryManager: Векторная база успешно загружена.")
        else:
            print(f"MemoryManager: Существующая база не найдена. Создание новой в '{VECTOR_STORE_PATH}'...")
            initial_text = "Начало памяти Нокса."
            initial_doc = [Document(page_content=initial_text)]
            self.vector_store = FAISS.from_documents(initial_doc, self.embeddings)
            self.vector_store.save_local(VECTOR_STORE_PATH)
            print("MemoryManager: Новая векторная база успешно создана и сохранена.")

    def _is_store_initialized(self) -> bool:
        """Проверяет, существуют ли файлы индекса FAISS."""
        index_file = Path(VECTOR_STORE_PATH) / "index.faiss"
        pkl_file = Path(VECTOR_STORE_PATH) / "index.pkl"
        return index_file.exists() and pkl_file.exists()

    def add_to_memory(self, text: str):
        """
        Добавляет новый текст в память.
        """
        print(f"MemoryManager: Добавление в память текста: '{text[:50]}...'")
        documents = self.text_splitter.create_documents([text])
        self.vector_store.add_documents(documents)
        self.vector_store.save_local(VECTOR_STORE_PATH)
        print("MemoryManager: Память успешно обновлена и сохранена.")

    def retrieve_from_memory(self, query: str, k: int = 3) -> List[str]:
        """
        Ищет в памяти k наиболее релевантных фрагментов для данного запроса.
        [ИЗМЕНЕНИЕ] Использует поиск с оценкой релевантности для лучшей отладки.
        """
        print(f"MemoryManager: Поиск в памяти по запросу: '{query}'")
        
        # [ИЗМЕНЕНИЕ] Используем similarity_search_with_score, чтобы видеть, насколько релевантны результаты.
        # FAISS использует L2-дистанцию, поэтому чем МЕНЬШЕ score, тем БОЛЕЕ релевантен документ.
        results_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
        
        print("MemoryManager: Результаты поиска с оценкой (чем меньше, тем лучше):")
        retrieved_texts = []
        for doc, score in results_with_scores:
            print(f"  - Score: {score:.4f}, Content: '{doc.page_content[:80]}...'")
            # [ИЗМЕНЕНИЕ] Добавляем "фильтр адекватности". Если результат слишком "далек" по смыслу (score > 0.7),
            # мы его отбрасываем. Этот порог (0.7) можно и нужно будет настраивать.
            if score < 0.7:
                 retrieved_texts.append(doc.page_content)

        print(f"MemoryManager: Найдено {len(retrieved_texts)} релевантных фрагментов после фильтрации.")
        return retrieved_texts
