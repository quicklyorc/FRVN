#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "${ROOT_DIR}/deploy/lib/gcp_common.sh"

require_env PROJECT_ID
require_env REGION
require_env SERVICE_NAME
require_env ARTIFACT_REPO
IMAGE_TAG="${IMAGE_TAG:-latest}"
FRONTEND_BUCKET="${FRONTEND_BUCKET:-${SERVICE_NAME}-bucket}"

ensure_apis
ensure_artifact_repo
IMAGE="$(build_and_push_backend)"

echo "Deploying Cloud Run service: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --port 8080 \
  --max-instances=5 \
  --cpu=1 \
  --memory=512Mi \
  --set-env-vars LOG_LEVEL="${LOG_LEVEL:-info}" \
  --set-env-vars GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"

echo "Preparing frontend bucket and CDN"
ensure_bucket
upload_frontend_dist
ensure_cdn_lb_for_bucket

echo "Cloud Run URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)'

echo "Done."


