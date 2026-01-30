FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

# Create non-root user
RUN adduser -D -s /bin/sh appuser

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Nginx needs to run as root to bind to port 80/3000, but worker processes can be non-root
RUN chown -R appuser:appuser /usr/share/nginx/html

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
