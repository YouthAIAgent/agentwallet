FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source files
COPY . .

# Expose dev server port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]
