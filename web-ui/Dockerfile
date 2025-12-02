# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
ARG BUILD_MODE=production
RUN npm run build

# Stage 2: Production - Serve with nginx
FROM nginx:alpine AS production
COPY --from=builder /app/dist/ragu-web-ui /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Development - Run dev server
FROM node:20-alpine AS development
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

EXPOSE 4200

# Start Angular dev server
CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "4200"]

