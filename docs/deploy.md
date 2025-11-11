Cloud Run/VM 배포

전제

- gcloud 인증 완료, 프로젝트/리전 설정
- Artifact Registry 권한

CLI로 export 후 배포

```bash
# 프로젝트 루트
cp .envexample .env   # 또는 env.example -> .env
export $(grep -v '^#' .env | xargs) || true

# deploy/ 스크립트 내보내기
frvn export deploy --to .

# Cloud Run
bash deploy/deploy_gcp_cloudrun.sh

# 또는 VM
bash deploy/deploy_gcp_vm.sh
```

CLI가 export와 실행을 한번에 처리

```bash
frvn deploy cloudrun   # 또는: frvn deploy vm
```

프런트는 GCS 버킷으로 업로드되며, HTTPS LB + CDN이 설정됩니다(도메인 제공 시).


