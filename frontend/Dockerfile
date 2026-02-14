# MedAudit Frontend - Vite build + nginx serve
# Stage 1: build
FROM node:22-alpine AS builder

RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

# Build args for Vite env (must be prefixed with VITE_)
ARG VITE_API_URL=/api
ARG VITE_BASENAME=
ARG VITE_GTM_ID=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASENAME=$VITE_BASENAME
ENV VITE_GTM_ID=$VITE_GTM_ID

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

# Stage 2: serve with nginx
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# SPA fallback: serve index.html for client-side routes (API is proxied by main nginx)
RUN echo 'server { listen 80; root /usr/share/nginx/html; index index.html; location / { try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
