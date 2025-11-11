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

INSTANCE_NAME="${SERVICE_NAME}-vm"
MACHINE_TYPE="e2-micro"
ZONE="${REGION}-a"

echo "Creating VM instance: ${INSTANCE_NAME}"
STARTUP_SCRIPT=$(cat <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
apt-get update && apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker && systemctl start docker
docker run -d --name {{SERVICE_NAME}} -p 80:8080 \
  -e LOG_LEVEL=${LOG_LEVEL:-info} \
  -e GUNICORN_WORKERS=${GUNICORN_WORKERS:-2} \
  {{IMAGE_URI}}
EOS
)

IMAGE_URI="${IMAGE}"
gcloud compute instances create "${INSTANCE_NAME}" \
  --project "${PROJECT_ID}" \
  --zone "${ZONE}" \
  --machine-type "${MACHINE_TYPE}" \
  --metadata=startup-script="$(echo "${STARTUP_SCRIPT}" | sed "s|{{IMAGE_URI}}|${IMAGE_URI}|g" | sed "s|{{SERVICE_NAME}}|${SERVICE_NAME}|g")" \
  --tags=http-server,https-server \
  --scopes=https://www.googleapis.com/auth/cloud-platform

echo "Opening firewall for HTTP/HTTPS"
gcloud compute firewall-rules create "${SERVICE_NAME}-allow-http" \
  --allow tcp:80 --target-tags http-server --project "${PROJECT_ID}" || true
gcloud compute firewall-rules create "${SERVICE_NAME}-allow-https" \
  --allow tcp:443 --target-tags https-server --project "${PROJECT_ID}" || true

echo "Preparing frontend bucket and CDN"
ensure_bucket
upload_frontend_dist
ensure_cdn_lb_for_bucket

echo "VM external IP:"
gcloud compute instances describe "${INSTANCE_NAME}" --zone "${ZONE}" --project "${PROJECT_ID}" --format='value(networkInterfaces[0].accessConfigs[0].natIP)'

echo "Done."


