FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml requirements.txt requirements-extra.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-extra.txt

COPY app ./app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]