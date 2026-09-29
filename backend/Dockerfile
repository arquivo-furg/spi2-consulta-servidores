FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py database.py gunicorn.conf.py ./

# A API só atende depois que a carga local termina sem erro.
CMD ["sh", "-c", "python db/bootstrap.py && exec gunicorn --config gunicorn.conf.py app:app"]
