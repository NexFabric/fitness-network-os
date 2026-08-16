# Build from repo `frontend/` context:
#   docker build -f scanner-pwa/Dockerfile --build-arg VITE_API_URL=https://api.example.com .
FROM node:26-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
COPY admin-web/package.json ./admin-web/
COPY scanner-pwa/package.json ./scanner-pwa/
RUN npm ci

COPY scanner-pwa ./scanner-pwa
WORKDIR /app/scanner-pwa
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/scanner-pwa/dist /usr/share/nginx/html
COPY scanner-pwa/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
