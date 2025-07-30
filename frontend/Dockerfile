FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Clean install
RUN rm -rf node_modules package-lock.json
RUN npm install

# Copy application files
COPY . .

EXPOSE 3000

# Use npx to run vite
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]
