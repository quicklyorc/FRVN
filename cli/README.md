# FRVN CLI

FRVN: FastAPI + React + Vite + Nginx 템플릿 프로젝트를 생성하고(GitHub 설치), GCP로 배포하는 스크립트를 export/실행하는 CLI입니다.

## 설치 (pipx via GitHub)

```bash
pipx install git+https://github.com/<org>/FRVN.git#subdirectory=cli
frvn --help
```

## 사용

```bash
# 도구 확인
frvn doctor

# 템플릿 생성
frvn init ./myapp --name myapp --service myapp

cd myapp
cp .envexample .env   # 또는 env.example -> .env
export $(grep -v '^#' .env | xargs) || true

# deploy 스크립트 export 후 수동 실행
frvn export deploy --to .
bash deploy/deploy_gcp_cloudrun.sh   # 또는 deploy/deploy_gcp_vm.sh

# export+실행을 한번에
frvn deploy cloudrun                 # 또는 frvn deploy vm
```


