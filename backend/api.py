import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from rag_service import AsyncRAG
from database import init_db
from schemas import ChatRequest


rag_service: AsyncRAG | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл API.
    При старте инициализирует все необходимые классы,
    при выключении закрывает все соединения.
    """

    global rag_service
    print("Starting API...")

    try:
        await init_db()
    except Exception as e:
        print(f"Error creating database tables: {e}")

    rag_service = AsyncRAG()
    await rag_service.initialize()

    yield

    print("Stopping API...")
    if rag_service:
        await rag_service.close()

app = FastAPI(title='FAS-helper API', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Основной эндпоинт для чата с поиском документов.

    Принимает JSON с запросом и историей чата (TODO).
    Возвращает поток NDJSON.
    """

    if not rag_service:
        return {"error": "Service not initialized"}
    
    stream_gen = rag_service.chat_stream(request.query)

    return StreamingResponse(
        stream_gen,
        media_type="application/x-ndjson"
    )

@app.get("/health")
async def health_check():
    """
    Проверка активности сервиса.
    """

    return {
        "status": "active",
        "rag_ready": rag_service is not None
    }


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
