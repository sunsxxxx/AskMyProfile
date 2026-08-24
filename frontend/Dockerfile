# syntax=docker/dockerfile:1

FROM node:22-alpine AS build
WORKDIR /app
ARG NPM_REGISTRY=https://registry.npmmirror.com
ENV PNPM_STORE_DIR=/pnpm/store
RUN --mount=type=cache,id=frontend-npm-cache,target=/root/.npm \
    npm install --global pnpm@11.19.0 --registry="${NPM_REGISTRY}" \
    && pnpm config set registry "${NPM_REGISTRY}"
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN --mount=type=cache,id=frontend-pnpm-store,target=/pnpm/store \
    pnpm config set store-dir "${PNPM_STORE_DIR}" \
    && pnpm fetch --frozen-lockfile
RUN --mount=type=cache,id=frontend-pnpm-store,target=/pnpm/store \
    pnpm config set store-dir "${PNPM_STORE_DIR}" \
    && pnpm install --offline --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM nginx:1.28-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
