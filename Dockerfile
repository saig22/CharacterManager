FROM python:3.11-slim

WORKDIR /character_manager

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run Flask
CMD ["flask", "run", "--host=0.0.0.0"]
