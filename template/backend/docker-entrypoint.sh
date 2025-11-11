#!/usr/bin/env bash
set -euo pipefail

# Render nginx conf with PORT env
envsubst '\n$PORT' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf

exec "$@"


