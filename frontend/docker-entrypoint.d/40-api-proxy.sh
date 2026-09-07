#!/bin/sh
# nginx:alpine runs every executable in /docker-entrypoint.d before starting
# nginx. Emit the /api/ proxy block only when $API_UPSTREAM is set.
set -e

target=/etc/nginx/conf.d/api_proxy.inc

if [ -n "$API_UPSTREAM" ]; then
    echo "40-api-proxy.sh: proxying /api/ to $API_UPSTREAM"
    cat > "$target" <<EOF
location /api/ {
    proxy_pass $API_UPSTREAM;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    client_max_body_size 6m;
}
EOF
else
    echo "40-api-proxy.sh: API_UPSTREAM unset, serving static assets only"
    : > "$target"
fi
