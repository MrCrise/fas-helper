import psycopg2
from typing import List, Dict, Any, Optional
from database import load_database_url


class TextFetcher:
    def __init__(self):
        self.db_url = load_database_url()
        if not self.db_url:
            raise ValueError("DATABASE_URL is missing in .env")

    def _get_text_with_cursor(self, cursor: Any, doc_id: str) -> Optional[str]:
        """Внутренний метод для получения текста через существующий курсор."""
        try:
            cursor.execute("SELECT full_text FROM documents WHERE doc_id = %s", (doc_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"SQL Error for doc_id {doc_id}: {e}")
            return None

    def get_full_text(self, doc_id: str) -> str:
        """Получает полный текст одного документа (открывает новое соединение)."""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            with conn.cursor() as cur:
                text = self._get_text_with_cursor(cur, doc_id)
                return text if text else ""
        except Exception as e:
            print(f"Connection error: {e}")
            return ""
        finally:
            if conn:
                conn.close()

    def fetch_full_texts(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Получает тексты для списка результатов.
        Оптимизация: использует одно соединение для всего пакета.
        """
        full_texts = []
        doc_ids = [res.get('doc_id') for res in results if res.get('doc_id')]

        if not doc_ids:
            return []

        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            with conn.cursor() as cur:
                for doc_id in doc_ids:
                    text = self._get_text_with_cursor(cur, doc_id)
                    if text:
                        full_texts.append(f"=== Документ ID: {doc_id} ===\n{text}")
                    else:
                        print(f"Text not found for doc_id: {doc_id}")
        except Exception as e:
            print(f"Batch fetch error: {e}")
        finally:
            if conn:
                conn.close()

        return full_texts