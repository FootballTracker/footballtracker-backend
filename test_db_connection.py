import asyncio
import asyncpg
import os
import ssl
from dotenv import load_dotenv

load_dotenv()


async def test_connection():
    try:
        ssl_context = ssl.create_default_context(cafile="ca.pem")

        conn = await asyncpg.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
            ssl=ssl_context,
        )
        print("Conexão a PostgreSQL sucedida!")
        await conn.close()
    except Exception as e:
        print(f"Erro ao conectar a PostgreSQL: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
