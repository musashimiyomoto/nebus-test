# Nebus API

REST API for Organizations Directory built with FastAPI, SQLAlchemy, and PostgreSQL.

## Requirements

- Docker and Docker Compose

## Setup and Running

1. Clone the repository:
```bash
git clone <repository-url>
cd organizations-directory-api
```

2. Create an environment file:
```bash
cp .env.sample .env
```

3. Edit the `.env` file with your settings.


4. Start the application with Docker Compose:
```bash
docker-compose up -d
```

5. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
