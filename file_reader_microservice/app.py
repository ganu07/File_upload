import aiofiles
import asyncio
import json
import aio_pika
import logging

RABBITMQ_HOST = 'rabbitmq'
QUEUE_NAME = 'data_queue'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting parameters
MESSAGE_DELAY = 0.1  # 100ms delay between each message
MAX_CONCURRENT_PUBLISHES = 10  # Limit to 10 concurrent publishing tasks

# Semaphore to limit concurrent tasks
semaphore = asyncio.Semaphore(MAX_CONCURRENT_PUBLISHES)

# Publish to RabbitMQ
async def publish_to_queue(data):
    # Establish an async connection to RabbitMQ
    connection = await aio_pika.connect_robust(f"amqp://{RABBITMQ_HOST}")
    
    # Create a channel from the connection
    async with connection:
        async with connection.channel() as channel:
            # Declare the queue (async)
            await channel.declare_queue(QUEUE_NAME, durable=True)
            
            # Publish the message to the queue (using the default exchange)
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(data).encode()),
                routing_key=QUEUE_NAME
            )
            
            # Log the data being sent
            logger.info(f"Sent: {data}")

# Rate-limited publish function
async def publish_to_queue_with_rate_limit(data):
    # Acquire the semaphore to limit concurrent tasks
    async with semaphore:
        await publish_to_queue(data)
        # Apply the message delay to rate limit the publishing speed
        await asyncio.sleep(MESSAGE_DELAY)

# Read a file asynchronously and publish its content
async def process_file(file_path):
    async with aiofiles.open(file_path, mode='r') as file:
        async for line in file:
            data = {"line": line.strip()}
            await publish_to_queue_with_rate_limit(data)

# Read multiple files concurrently
async def read_multiple_files(file_paths):
    tasks = [process_file(file_path) for file_path in file_paths]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    file_paths = ['/data/data1.txt', "/data/data2.txt"]  # Example file paths
    logger.info(f"Starting to process files: {file_paths}")
    asyncio.run(read_multiple_files(file_paths))
    logger.info("File processing complete.")
