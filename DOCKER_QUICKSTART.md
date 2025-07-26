# Docker Quick Start Guide

This guide will help you get the OptimizeDeFi application running quickly using Docker.

## Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop/))
- Git installed
- A 1inch API key (get one at [1inch Developer Portal](https://portal.1inch.dev/))

## Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd optimizedefi
```

### 2. Set up environment variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your 1inch API key
# ONEINCH_API_KEY=your_api_key_here
```

### 3. Start the application
```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 4. Access the application

Once the containers are running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

## Common Docker Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
```

### Stop the application
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Rebuild after code changes
```bash
# Rebuild and restart
docker-compose up --build

# Rebuild specific service
docker-compose build frontend
docker-compose up frontend
```

### Access container shell
```bash
# Frontend container
docker-compose exec frontend sh

# Backend container
docker-compose exec backend bash
```

## Development Workflow

### Frontend Development
The frontend uses volume mounting, so changes to your code will be reflected immediately thanks to Next.js hot reload.

### Backend Development
The backend also uses volume mounting and runs with `--reload` flag, so FastAPI will automatically restart when you make changes.

### Installing new dependencies

#### Frontend (npm packages)
```bash
# Option 1: Install locally first
cd frontend
npm install package-name

# Option 2: Install in container
docker-compose exec frontend npm install package-name
```

#### Backend (Python packages)
```bash
# Update pyproject.toml, then rebuild
docker-compose build backend
docker-compose up backend
```

## Troubleshooting

### Port already in use
If you get a "port already in use" error:
```bash
# Find and kill the process using the port
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
```

### Container won't start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Permission issues
If you encounter permission issues:
```bash
# Fix ownership (run from project root)
sudo chown -R $USER:$USER .
```

### Out of space
```bash
# Clean up Docker resources
docker system prune -a --volumes
```

## Production Build

For production deployment:

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run production containers
docker-compose -f docker-compose.prod.yml up -d
```

## Next Steps

1. Verify the frontend loads at http://localhost:3000
2. Check the API health at http://localhost:8000/health
3. Explore the API documentation at http://localhost:8000/docs
4. Start developing! The hot reload will handle most changes automatically.

## Need Help?

- Check the logs: `docker-compose logs -f`
- Ensure your .env file has the correct API keys
- Make sure Docker Desktop is running
- Try rebuilding: `docker-compose down && docker-compose up --build`