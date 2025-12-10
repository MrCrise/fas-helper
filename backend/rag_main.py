import os
import asyncio
from rag_service import AsyncRAG


async def main():
    rag = AsyncRAG()

    try:
        await rag.initialize()
        print("RAG is ready for work. Type 'exit' for exit.")

        while True:
            user_input = input("Your query >> ").strip()

            if user_input.lower() in ['exit', 'quit', 'выход']:
                break

            if not user_input:
                continue

            await rag.terminal_stream(user_input)

    except KeyboardInterrupt:
        print("\nForce interruption")
    except Exception as e:
        print(f"\nCritical error: {e}")
    finally:
        await rag.close()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
