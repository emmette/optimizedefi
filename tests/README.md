# Testing Guide

This guide explains how to run tests for the OptimizeDeFi application.

## Backend Tests

### Running All Backend Tests

```bash
# From the project root
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/api/test_chat_websocket.py

# Run with verbose output
docker-compose exec backend pytest -v
```

### Backend Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures and configuration
├── api/
│   ├── test_auth.py         # Authentication endpoint tests
│   └── test_chat_websocket.py # WebSocket chat tests
├── workflows/
│   └── test_chat_workflow.py # Chat workflow tests
└── integration/
    └── test_chat_e2e.py     # End-to-end integration tests
```

### Running Specific Test Categories

```bash
# Unit tests only
docker-compose exec backend pytest tests/api tests/workflows

# Integration tests only
docker-compose exec backend pytest tests/integration

# Tests matching a pattern
docker-compose exec backend pytest -k "websocket"
```

## Frontend Tests

### Running Frontend Tests

```bash
# From the frontend directory
cd frontend
npm test

# Run tests in CI mode (no watch)
npm run test:ci

# With coverage
npm test -- --coverage

# Run specific test file
npm test useChat.test.tsx
```

### Frontend Test Structure

```
frontend/__tests__/
├── hooks/
│   └── useChat.test.tsx     # Chat hook tests
└── lib/
    └── api/
        └── chat.test.ts     # WebSocket client tests
```

## Manual Testing

### Test Chat Service

A test script is provided to verify the chat service is working:

```bash
# Basic test
python scripts/test_chat_service.py

# With async WebSocket test
python scripts/test_chat_service.py --async
```

This script will:
1. Check backend health
2. Test WebSocket connection
3. Send a test message and verify response
4. Report results

### Expected Output

```
🚀 Starting Chat Service Tests
==================================================
✅ Backend health check passed
✅ WebSocket connection established
   Welcome message: Welcome to OptimizeDeFi AI assistant...
📤 Sent message: What is DeFi?
✅ Received typing indicator
✅ Received AI response
   Content: DeFi stands for Decentralized Finance...
   Agent: general

==================================================
📊 Test Summary:
   Health Check: ✅ PASS
   WebSocket Connection: ✅ PASS
   Chat Interaction: ✅ PASS
   Authenticated Chat: ✅ PASS

Total: 4/4 tests passed
```

## Test Coverage

### Backend Coverage

```bash
# Generate coverage report
docker-compose exec backend pytest --cov=app --cov-report=html

# View coverage report
open backend/htmlcov/index.html
```

### Frontend Coverage

```bash
# Generate coverage report
cd frontend
npm test -- --coverage --watchAll=false

# View coverage report
open frontend/coverage/lcov-report/index.html
```

## Environment Variables for Testing

Backend tests use these environment variables:
- `OPENROUTER_API_KEY`: Required for chat workflow tests
- `ONE_INCH_API_KEY`: Optional for 1inch integration tests
- `DATABASE_URL`: Test database connection

Frontend tests mock all external dependencies.

## Debugging Tests

### Backend

```bash
# Run with debugging output
docker-compose exec backend pytest -vv -s

# Run with pdb on failure
docker-compose exec backend pytest --pdb

# Run specific test with full output
docker-compose exec backend pytest tests/api/test_chat_websocket.py::TestChatWebSocket::test_websocket_connection_unauthenticated -vv
```

### Frontend

```bash
# Run in debug mode
cd frontend
node --inspect-brk node_modules/.bin/jest --runInBand

# Run single test in watch mode
npm test -- --watch useChat.test.tsx
```

## CI/CD Integration

For CI/CD pipelines:

```bash
# Backend
docker-compose run --rm backend pytest --cov=app --cov-report=xml

# Frontend  
cd frontend && npm run test:ci -- --coverage --coverageReporters=lcov
```

## Common Issues

1. **WebSocket tests failing**: Ensure the backend is running and CORS is configured correctly
2. **Chat workflow tests failing**: Check that OPENROUTER_API_KEY is set in .env
3. **Frontend tests failing**: Run `npm install` to ensure all dependencies are installed
4. **Rate limit errors**: Tests may hit rate limits if run too frequently

## Writing New Tests

### Backend Test Example

```python
# tests/api/test_new_endpoint.py
import pytest
from fastapi.testclient import TestClient

def test_new_endpoint(client: TestClient):
    response = client.get("/api/new-endpoint")
    assert response.status_code == 200
```

### Frontend Test Example

```typescript
// __tests__/components/NewComponent.test.tsx
import { render, screen } from '@testing-library/react'
import { NewComponent } from '@/components/NewComponent'

describe('NewComponent', () => {
  it('renders correctly', () => {
    render(<NewComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```