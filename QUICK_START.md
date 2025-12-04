# Quick Start Guide

## Project Overview

This is an event-driven microservices architecture for processing e-commerce orders. It demonstrates:

- Event-driven communication between services
- Message queue patterns (Redis Streams)
- Service separation and independence
- Real-time updates via WebSocket

## Architecture Flow

```
1. User creates order → API Gateway
2. API Gateway → Publishes OrderCreated event → Redis Stream
3. Order Service → Consumes event → Processes order → Publishes OrderStatusUpdated
4. Notification Service → Consumes OrderStatusUpdated → Sends email
5. WebSocket → Pushes status updates to frontend (in progress)
```

## Quick Setup (5 minutes)

### 1. Start Infrastructure

```bash
docker-compose up -d
```

### 2. Setup API Gateway

```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../../shared
python manage.py migrate
python manage.py runserver 8000
```

### 3. Setup Order Service (new terminal)

```bash
cd services/order-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../../shared
python manage.py migrate
python manage.py consume_events
```

### 4. Setup Notification Service (new terminal)

```bash
cd services/notification-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../../shared
python manage.py migrate
# Configure EMAIL_* settings in .env or settings.py
python manage.py consume_events
```

### 5. Test It!

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "products": [{"product_id": "223e4567-e89b-12d3-a456-426614174000", "quantity": 2, "price": 29.99}],
    "shipping_address": "123 Main St",
    "user_email": "test@example.com"
  }'
```

Watch the logs in each service terminal to see the event flow!

## Key Files

- `shared/events/` - Event schemas (shared across all services)
- `services/api-gateway/` - Entry point, publishes OrderCreated
- `services/order-service/` - Processes orders, publishes OrderStatusUpdated
- `services/notification-service/` - Sends email notifications

## Common Commands

```bash
# Check Redis Stream
docker exec -it <redis-container> redis-cli XREAD STREAMS orders 0

# Check consumer groups
docker exec -it <redis-container> redis-cli XINFO GROUPS orders

# Django admin
# http://localhost:8000/admin (API Gateway)
```

## Next Steps

1. Read `ARCHITECTURE.md` for design decisions
2. Read `IMPROVEMENTS.md` for future enhancements
3. Implement WebSocket real-time updates
4. Add more services (Payment, Inventory, Shipping)

## Troubleshooting

- **Can't connect to Redis**: Check `docker-compose ps`
- **Events not processing**: Make sure consumers are running
- **Email not sending**: Configure EMAIL\_\* settings

See `SETUP.md` for detailed troubleshooting.
