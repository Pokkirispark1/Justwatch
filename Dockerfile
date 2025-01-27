FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the destination is explicitly a directory by adding a trailing slash
COPY src/*.py ./

CMD ["python", "main.py"]
