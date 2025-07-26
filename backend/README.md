# OptimizeDeFi Backend

FastAPI backend for the OptimizeDeFi AI-powered DeFi portfolio manager.

## Setup

### Using pip with pyproject.toml

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp ../.env.example .env
```

Required variables:
- `ONEINCH_API_KEY`: Your 1inch API key
- `JWT_SECRET`: Secret key for JWT tokens

## Running the Server

### Development mode (with auto-reload):
```bash
python -m uvicorn app.main:app --reload
# or
python -m app.main
```

### Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core configuration and utilities
│   ├── models/       # Pydantic models
│   ├── services/     # Business logic
│   └── main.py       # FastAPI application
├── tests/            # Test files
├── pyproject.toml    # Project dependencies and configuration
└── README.md
```