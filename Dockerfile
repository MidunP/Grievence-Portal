# Use multi-stage Python + Node.js image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_VERSION=20.x \
    PORT=3000

WORKDIR /app

# Install system dependencies & Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json and install Node dependencies
COPY package*.json ./
RUN npm install --production

# Copy application source code
COPY . .

# Generate synthetic dataset and train ML baseline models if missing
RUN python data_generator.py && python train_models.py

# Expose port
EXPOSE 3000 8000

# Default command starts the Express backend
CMD ["node", "server.js"]
