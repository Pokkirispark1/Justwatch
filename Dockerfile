FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'src' folder into the container
COPY src/ ./src/

CMD ["python", "src/main.py"]
