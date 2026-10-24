FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Wheels exist for asyncpg/bcrypt on slim, so no compiler toolchain is needed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY deploy/start.sh ./start.sh
RUN sed -i 's/\r$//' start.sh

RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Hosts like Render/Railway/Fly inject $PORT; start.sh falls back to 8000.
CMD ["sh", "start.sh"]
