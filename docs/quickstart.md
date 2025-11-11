개요

- 로컬 개발은 docker-compose.dev.yml을 사용합니다. venv는 사용하지 않습니다.

시작하기

1) 템플릿 생성

```bash
frvn init ./myapp --name myapp --service myapp
```

2) 개발 실행

```bash
cd myapp
cp .envexample .env
docker compose -f docker-compose.dev.yml up -d --build
```

프런트: http://localhost:5173, 백엔드: http://localhost:8000

배포

```bash
frvn export deploy --to .
export $(grep -v '^#' .env | xargs) || true
bash deploy/deploy_gcp_cloudrun.sh   # 또는 deploy/deploy_gcp_vm.sh
```


