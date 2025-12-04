# Setup Guide

This guide will help you set up and run the event-driven architecture project.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for Redis and PostgreSQL)
- Node.js 18+ (for React frontend - optional for now)

## Step 1: Start Infrastructure Services

Start Redis and PostgreSQL using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- Redis on port 6379
- PostgreSQL for API Gateway on port 5432
- PostgreSQL for Order Service on port 5433
- PostgreSQL for Notification Service on port 5434

Verify services are running:
```bash
docker-compose ps
```

## Step 2: Set Up API Gateway Service

```bash
cd services/api-gateway

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install shared events module
pip install -e ../../shared

# Set up environment variables
cp .env.example .env  # Create if needed, or set manually:
# DB_NAME=api_gateway_db
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_HOST=localhost
# DB_PORT=5432
# REDIS_HOST=localhost
# REDIS_PORT=6379

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start the server
python manage.py runserver 8000
```

## Step 3: Set Up Order Service

Open a new terminal:

```bash
cd services/order-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install shared events module
pip install -e ../../shared

# Set up environment variables
# DB_NAME=order_service_db
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_HOST=localhost
# DB_PORT=5432
# REDIS_HOST=localhost
# REDIS_PORT=6379
# EVENT_STREAM_NAME=orders
# CONSUMER_GROUP=order-processors
# CONSUMER_NAME=order-processor-1

# Run migrations
python manage.py migrate

# Start the event consumer (this will run continuously)
python manage.py consume_events
```

## Step 4: Set Up Notification Service

Open another new terminal:

```bash
cd services/notification-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install shared events module
pip install -e ../../shared

# Set up environment variables
# DB_NAME=notification_service_db
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_HOST=localhost
# DB_PORT=5432
# REDIS_HOST=localhost
# REDIS_PORT=6379
# EVENT_STREAM_NAME=orders
# CONSUMER_GROUP=notification-processors
# CONSUMER_NAME=notification-processor-1
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
# DEFAULT_FROM_EMAIL=noreply@example.com

# Run migrations
python manage.py migrate

# Start the event consumer (this will run continuously)
python manage.py consume_events
```

## Step 5: Test the System

### Create an Order

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "products": [
      {
        "product_id": "223e4567-e89b-12d3-a456-426614174000",
        "quantity": 2,
        "price": 29.99,
        "name": "Test Product"
      }
    ],
    "shipping_address": "123 Main St, City, Country",
    "user_email": "test@example.com"
  }'
```

### Check Order Status

```bash
curl http://localhost:8000/api/orders/{order_id}/
```

### Monitor Events

You can monitor Redis Streams to see events:

```bash
docker exec -it <redis-container-id> redis-cli
XREAD STREAMS orders 0
```

## Troubleshooting

### Issue: Cannot connect to Redis
- Make sure Redis is running: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`

### Issue: Cannot connect to PostgreSQL
- Make sure PostgreSQL containers are running
- Check database logs: `docker-compose logs postgres-api-gateway`

### Issue: Events not being consumed
- Make sure the consumer commands are running
- Check Redis Stream: `redis-cli XINFO STREAM orders`
- Check consumer groups: `redis-cli XINFO GROUPS orders`

### Issue: Email not sending
- Configure email settings in notification service `.env`
- For Gmail, use an App Password, not your regular password
- Check notification service logs for errors

## Development Tips

1. **Watch Logs**: Each service logs events - watch the console output
2. **Django Admin**: Access admin panels at:
   - API Gateway: http://localhost:8000/admin
   - Order Service: http://localhost:8001/admin (if you run it)
   - Notification Service: http://localhost:8002/admin (if you run it)
3. **Redis CLI**: Use `docker exec -it <redis-container> redis-cli` to inspect streams
4. **Database Access**: Use `psql` or a GUI tool to inspect databases

## Next Steps

1. Set up the React frontend
2. Implement WebSocket real-time updates
3. Add more event types
4. Add error handling and retries
5. Add monitoring and observability

