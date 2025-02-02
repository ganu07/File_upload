import aio_pika
import asyncio
import asyncpg
import json
import os
import logging

RABBITMQ_HOST = 'rabbitmq'
QUEUE_NAME = os.getenv("QUEUE_NAME", "data_queue")
POSTGRES_CONFIG = {
    'user': 'user',
    'password': 'password',
    'database': 'file_db',
    'host': 'postgres',
    'port': 5432,
}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_db_connection():
    logger.info("Connecting to PostgreSQL...")
    return await asyncpg.connect(**POSTGRES_CONFIG)

async def create_table_if_not_exists(db_connection):
    logger.info("Creating table if it doesn't exist...")
    await db_connection.execute("""
        CREATE TABLE IF NOT EXISTS file_data (
            id SERIAL PRIMARY KEY,
            line_data TEXT NOT NULL
        )
    """)
    logger.info("Table setup complete.")

async def process_message(message, db_connection):
    try:
        data = json.loads(message.body)
        logger.info(f"Received message: {data}")
        
        await db_connection.execute(
            "INSERT INTO file_data (line_data) VALUES ($1)",
            data['line']
        )
        logger.info(f"Inserted into DB: {data}")
        await message.ack()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.nack(requeue=False)

async def consume_messages():
    try:
        logger.info("Connecting to RabbitMQ...")
        connection = await aio_pika.connect_robust(f"amqp://{RABBITMQ_HOST}")
        async with connection:
            logger.info("Connected to RabbitMQ.")
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            logger.info(f"Declared queue: {QUEUE_NAME}")

            db_connection = await get_db_connection()
            await create_table_if_not_exists(db_connection)
            logger.info("Consuming messages...")

            async for message in queue:
                await process_message(message, db_connection)
    except Exception as e:
        logger.error(f"Error consuming messages: {e}")

if __name__ == "__main__":
    asyncio.run(consume_messages())
