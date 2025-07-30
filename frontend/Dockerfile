# frontend/Dockerfile
FROM node:20-slim

# Install dependencies for native modules
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with force to ensure proper architecture
RUN npm install --force --loglevel verbose

# Copy application code
COPY . .

EXPOSE 5173

# Default command (overridden by docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]