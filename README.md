# README: Microservices Project

## Overview
This project demonstrates a microservices architecture with the following components:

1. **File Reader Microservice**:
   - Reads multiple files asynchronously.
   - Publishes data line-by-line to RabbitMQ.

2. **Data Consumer Microservice**:
   - Consumes messages from RabbitMQ.
   - Stores the data in a PostgreSQL database.

3. **API Microservice**:
   - Exposes an API to search, filter, and paginate the data.
   - Implements rate limiting using Redis.

The system is fully containerized using Docker and Docker Compose.

---

## Prerequisites

1. Install [Docker](https://www.docker.com/).
2. Install [Docker Compose](https://docs.docker.com/compose/).
3. Clone this repository to your local machine.

---

## How to Run the Project

1. Navigate to the project root directory:
   ```bash
   cd project
   ```

2. Start all services using Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Verify the services:
   - RabbitMQ Management UI: [http://localhost:15672](http://localhost:15672) (default username: `guest`, password: `guest`)
   - API Microservice: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger documentation)

4. Place your data files in the `data/` directory to be processed by the File Reader Microservice.

---

## API Endpoints

The API Microservice exposes the following endpoints:

### **GET /data**
Fetch paginated data with optional search and filter capabilities.

#### Query Parameters:
- `pageno` (int): Page number (default: 1)
- `pagesize` (int): Number of items per page (default: 10)
- `name` (str): Filter by matching lines containing this string (default: none)

#### Example:
```bash
curl -X GET "http://localhost:8000/data?pageno=1&pagesize=5&name=example"
```

Response:
```json
[
  {"id": 1, "line_data": "example line 1"},
  {"id": 2, "line_data": "example line 2"}
]
```

### **Rate Limiting**
Each client is allowed 100 requests per minute. Exceeding this limit will result in a `429 Too Many Requests` error.

---

## System Flow

1. **File Reader Microservice**:
   - Reads files asynchronously from the `data/` directory.
   - Publishes each line to RabbitMQ.

2. **Data Consumer Microservice**:
   - Listens to RabbitMQ.
   - Inserts each received message into the PostgreSQL database.

3. **API Microservice**:
   - Provides search, filter, and pagination for stored data.
   - Implements rate limiting using Redis.

---

## Example Workflow

1. Place text files (`data1.txt`, `data2.txt`, etc.) in the `data/` directory.
2. Start the system with Docker Compose.
3. Verify that data is being processed:
   - Check RabbitMQ logs for published messages.
   - Verify data insertion in PostgreSQL using the API or a database client.
4. Query data through the API:
   ```bash
   curl -X GET "http://localhost:8000/data?pageno=1&pagesize=10"
   ```

---

## Stopping the Services

To stop all running services, press `Ctrl+C` in the terminal or run:
```bash
docker-compose down
```

---

## Troubleshooting

1. **RabbitMQ not reachable**:
   - Ensure the RabbitMQ container is running: `docker ps`.
   - Check logs: `docker-compose logs rabbitmq`.

2. **PostgreSQL connection issues**:
   - Verify the database credentials in `.env`.
   - Check logs: `docker-compose logs postgres`.

3. **Rate limit exceeded**:
   - Wait for the rate limit to reset (1 minute).

4. **File Reader not processing files**:
   - Ensure files are placed in the `data/` directory.
   - Check the File Reader logs: `docker-compose logs file_reader`.

---

## Environment Variables

Environment variables are defined in the `.env` file:

```plaintext
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=file_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
```

Update these values as needed.

---

## Database Setup

The PostgreSQL database will automatically create the `file_data` on first run. Its schema is:

```sql
CREATE TABLE file_data (
    id SERIAL PRIMARY KEY,
    line_data TEXT NOT NULL
);
```
