from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import URL, select, MetaData, Table
from sqlalchemy.engine.url import make_url


class AsyncDocumentFetcher:
    def __init__(self, database_url: str):
        url: URL = make_url(database_url)
        if url.drivername == 'postgresql':
            url = url.set(drivername='postgresql+asyncpg')

        self.engine = create_async_engine(url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False)

        self._documents_table: Optional[Table] = None

    async def _get_table(self) -> Table:
        """
        Возвращает таблицу с документами.
        При первом вызове также инициализирует её.
        """

        if self._documents_table is None:
            metadata = MetaData()
            async with self.engine.begin() as conn:
                await conn.run_sync(metadata.reflect)
                self._documents_table = metadata.tables['documents']

        return self._documents_table

    async def get_texts_by_ids(self, doc_ids: List[str]) -> Dict[str, str]:
        """
        Получает полные текста документов по их ID одним запросом.
        """

        if not doc_ids:
            return {}

        table = await self._get_table()

        async with self.async_session() as session:
            statement = select(table.c.doc_id, table.c.full_text).where(
                table.c.doc_id.in_(doc_ids))

            result = await session.execute(statement)
            rows = result.fetchall()

            return {row.doc_id: row.full_text for row in rows if row.full_text}

    async def close(self) -> None:
        """
        Закрывает соединение с БД.
        """

        await self.engine.dispose()
