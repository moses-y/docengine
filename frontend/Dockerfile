# Build the static bundle...
FROM node:20-alpine AS build
WORKDIR /srv
COPY package.json ./
RUN npm install
COPY . .

# Vite inlines VITE_* variables into the bundle at build time, so the API base
# URL has to be a build arg, not a runtime env var. Default "/api" keeps the
# compose setup (nginx proxying /api to the api service) working unchanged;
# deploys where the API lives on its own domain pass an absolute URL instead.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ...then serve it with nginx.
FROM nginx:alpine
COPY --from=build /srv/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/40-api-proxy.sh /docker-entrypoint.d/40-api-proxy.sh
# nginx refuses to load a config whose include target is missing, so ship an
# empty one; 40-api-proxy.sh overwrites it at start when $API_UPSTREAM is set.
RUN chmod +x /docker-entrypoint.d/40-api-proxy.sh \
    && touch /etc/nginx/conf.d/api_proxy.inc
EXPOSE 80
