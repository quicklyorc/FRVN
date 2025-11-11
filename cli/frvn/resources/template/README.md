{{PROJECT_NAME}} - FRVN 템플릿 기반 프로젝트

## 로컬 개발

```bash
cp .envexample .env
docker compose -f docker-compose.dev.yml up -d --build
```

- 프런트: http://localhost:5173
- 백엔드: http://localhost:8000
- 헬스체크: http://localhost:8000/healthz (또는 프론트에서 /api/healthz 프록시)

## 프로덕션 유사 실행

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 배포(GCP)

상위 리포지토리의 `deploy/` 스크립트를 참고하세요. 일반적으로:

```bash
export PROJECT_ID=...
export REGION=...
export SERVICE_NAME={{SERVICE_NAME}}
export ARTIFACT_REPO={{ARTIFACT_REPO}}
export IMAGE_TAG={{IMAGE_TAG}}

# Cloud Run
bash deploy/deploy_gcp_cloudrun.sh

# 또는 VM
bash deploy/deploy_gcp_vm.sh
```



