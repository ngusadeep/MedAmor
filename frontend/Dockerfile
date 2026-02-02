# MedAudit Frontend - Build with Node 22, serve with Nginx
# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

COPY . .

# Build-time env for API base URL (nginx will proxy /api to backend)
ARG VITE_API_URL=/api
ARG VITE_BASENAME=
ARG VITE_GTM_ID=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASENAME=$VITE_BASENAME
ENV VITE_GTM_ID=$VITE_GTM_ID

RUN pnpm run build

# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy frontend nginx config (SPA fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
