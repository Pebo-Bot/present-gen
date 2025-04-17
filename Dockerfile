# Use a slim Python base
FROM python:3.10-slim

# Install pandoc
RUN apt-get update \
 && apt-get install -y pandoc \
 && rm -rf /var/lib/apt/lists/*

# Copy in your code
WORKDIR /app
COPY . .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose & run
EXPOSE 5000
CMD ["python", "app.py"]
