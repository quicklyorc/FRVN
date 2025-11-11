#!/usr/bin/env bash
set -euo pipefail

require_env() {
  local key="$1"
  if [ -z "${!key:-}" ]; then
    echo "Missing required env: $key" >&2
    exit 1
  fi
}

ensure_apis() {
  gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    compute.googleapis.com \
    --project "${PROJECT_ID}"
}

ensure_artifact_repo() {
  local repo="${ARTIFACT_REPO}"
  if ! gcloud artifacts repositories describe "$repo" --location "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$repo" \
      --repository-format=docker \
      --location "${REGION}" \
      --project "${PROJECT_ID}"
  fi
}

build_and_push_backend() {
  local image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${SERVICE_NAME}:${IMAGE_TAG}"
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
  docker build -t "${image}" -f backend/Dockerfile.backend backend
  docker push "${image}"
  echo "${image}"
}

ensure_bucket() {
  local bucket="${FRONTEND_BUCKET}"
  if ! gsutil ls -b "gs://${bucket}" >/dev/null 2>&1; then
    gsutil mb -l "${REGION}" "gs://${bucket}"
  fi
  gsutil iam ch allUsers:objectViewer "gs://${bucket}"
}

upload_frontend_dist() {
  local bucket="${FRONTEND_BUCKET}"
  (cd frontend && npm ci && npm run build)
  gsutil -m rsync -r -d frontend/dist "gs://${bucket}"
  gsutil -m setmeta -h "Cache-Control:public, max-age=${CACHE_TTL:-3600}" "gs://${bucket}/**" || true
}

ensure_cdn_lb_for_bucket() {
  local bucket="${FRONTEND_BUCKET}"
  local url_map="${SERVICE_NAME}-urlmap"
  local backend_bucket="${SERVICE_NAME}-backend-bucket"
  local cdn_policy="--enable-cdn --cache-mode=CACHE_ALL_STATIC"

  if ! gcloud compute backend-buckets describe "${backend_bucket}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud compute backend-buckets create "${backend_bucket}" \
      --gcs-bucket-name="${bucket}" \
      ${cdn_policy} \
      --project "${PROJECT_ID}"
  fi

  if ! gcloud compute url-maps describe "${url_map}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud compute url-maps create "${url_map}" \
      --default-backend-bucket="${backend_bucket}" \
      --project "${PROJECT_ID}"
  fi

  if [ -n "${FRONTEND_DOMAIN:-}" ]; then
    local cert="${SERVICE_NAME}-managed-cert"
    local proxy="${SERVICE_NAME}-https-proxy"
    local frule="${SERVICE_NAME}-https-frule"
    local global_ip="${SERVICE_NAME}-ip"

    gcloud compute addresses describe "${global_ip}" --global --project "${PROJECT_ID}" >/dev/null 2>&1 || \
      gcloud compute addresses create "${global_ip}" --global --project "${PROJECT_ID}"

    gcloud compute ssl-certificates describe "${cert}" --project "${PROJECT_ID}" >/dev/null 2>&1 || \
      gcloud compute ssl-certificates create "${cert}" --domains "${FRONTEND_DOMAIN}" --project "${PROJECT_ID}"

    gcloud compute target-https-proxies describe "${proxy}" --project "${PROJECT_ID}" >/dev/null 2>&1 || \
      gcloud compute target-https-proxies create "${proxy}" --ssl-certificates "${cert}" --url-map "${url_map}" --project "${PROJECT_ID}"

    gcloud compute forwarding-rules describe "${frule}" --global --project "${PROJECT_ID}" >/dev/null 2>&1 || \
      gcloud compute forwarding-rules create "${frule}" --address "${global_ip}" --global --target-https-proxy "${proxy}" --ports 443 --project "${PROJECT_ID}"
  fi
}


