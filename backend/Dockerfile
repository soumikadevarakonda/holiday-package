FROM python:3.12-slim

WORKDIR /srv/backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY pytest.ini .

# data/ and database/ are mounted by docker-compose at /srv/data and /srv/database
ENV DATA_DIR=/srv/data DATABASE_DIR=/srv/database

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
