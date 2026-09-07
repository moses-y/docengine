# Build the static bundle...
FROM node:20-alpine AS build
WORKDIR /srv
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# ...then serve it with nginx, proxying /api to the backend service.
FROM nginx:alpine
COPY --from=build /srv/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
