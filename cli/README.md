# FRVN CLI

FRVN: FastAPI + React + Vite + Nginx 템플릿 프로젝트를 생성하고(GitHub 설치), GCP로 배포하는 스크립트를 export/실행하는 CLI입니다.

## 설치 (pipx via GitHub)

```bash
pipx install git+https://github.com/quicklyorc/FRVN.git#subdirectory=cli
frvn --help
```

## 사용

```bash
# 도구 확인
frvn doctor

# 템플릿 생성 (현재 폴더)
mkdir myapp && cd myapp
frvn init

cd myapp
cp .envexample .env   # 설명이 포함된 예시를 .env로 복사
export $(grep -v '^#' .env | xargs) || true

# 로컬 개발
docker compose -f docker-compose.dev.yml up -d --build

# 배포(Cloud Run)
frvn deploy cloudrun                 # (또는 frvn deploy vm)
```

### 참고
- `frvn init`은 현재 폴더에 템플릿을 생성하고 `.envexample`, `deploy/` 스크립트를 자동으로 배치합니다.
- `.envexample`에는 각 환경변수의 용도가 주석으로 설명되어 있습니다.
- `frvn deploy <target>`은 필요한 스크립트를 자동 export하고 `.env`를 로드하여 배포를 수행합니다.
