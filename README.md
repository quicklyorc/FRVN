FRVN: FastAPI + React + Vite + Nginx 모노 템플릿

개발은 Docker(venv 미사용), dev는 docker-compose, prod는 멀티스테이지 Dockerfile, 운영 시 백엔드 컨테이너 내부 Nginx가 리버스 프록시/LB 역할을 수행합니다. GCP 배포 스크립트(Cloud Run, VM)와 정적 프론트(GCS+CDN) 자동화를 제공합니다.

## 설치/사용

CLI를 컨테이너로 실행하거나, pipx로 설치하여 사용합니다.

### 컨테이너로 CLI 사용

```bash
docker build -t frvn-cli -f cli/Dockerfile cli
docker run --rm -v "$PWD:/work" -w /work frvn-cli init ./myapp --name myapp --service myapp
```

### pipx로 설치 (GitHub)

```bash
pipx install git+https://github.com/quicklyorc/FRVN.git#subdirectory=cli
frvn doctor                       # 도구 확인
frvn init ./myapp --name myapp --service myapp
```

릴리스 태그에서 설치(권장):

```bash
pipx install "git+https://github.com/quicklyorc/FRVN.git@v0.1.1#subdirectory=cli"
```

## CLI 명령 요약

프로젝트 생성을 최소 복사로 유지하고, 필요 시 배포 스크립트만 내보내거나(Export) 바로 배포까지 실행할 수 있습니다.

```bash
# 로컬 도구 검증 (docker/gcloud/node/npm/python3)
frvn doctor

# 템플릿에서 새 프로젝트 생성
frvn init ./myapp --name myapp --service myapp --artifact-repo frvn-repo --image-tag latest

# 프로젝트에 배포 스크립트 export (deploy/ 생성)
cd myapp
frvn export deploy --to .            # 이미 존재하면 --force로 덮어쓰기

# CLI가 export → 배포 스크립트 실행까지 자동 수행
frvn deploy cloudrun                 # 또는: frvn deploy vm
# 옵션:
#   --project-root .     # 백엔드/프론트가 있는 루트 지정
#   --no-export          # export 생략(이미 deploy/가 있을 때)
#   --force-export       # export 강제 덮어쓰기
```

사전 준비

- `.envexample` → `.env`로 복사 후 값 채움(일부 환경에서는 `env.example`가 생성될 수 있음)
- `export $(grep -v '^#' .env | xargs) || true`로 환경 로드
- `gcloud auth login && gcloud config set project $PROJECT_ID` 등 GCP 기본 설정

## 이 패키지를 설치/빌드했을 때의 디렉토리 구조와 산출물

### 리포지토리(패키지) 구조

```text
.
├─ cli/                      # FRVN CLI 패키지 (pipx 설치 가능)
│  ├─ frvn/                  # 엔트리포인트 (__main__.py)
│  ├─ pyproject.toml         # 패키징 메타
│  └─ Dockerfile             # CLI 컨테이너 빌드
├─ template/                 # 실제 생성될 프로젝트 스캐폴드(읽기전용 원본)
│  ├─ backend/               # FastAPI + Nginx + Supervisor
│  ├─ frontend/              # React + Vite + Tailwind
│  ├─ .envexample
│  ├─ docker-compose.dev.yml
│  ├─ docker-compose.prod.yml
│  └─ README.md
├─ deploy/                   # 배포 스크립트
│  ├─ deploy_gcp_cloudrun.sh # Cloud Run 자동배포
│  ├─ deploy_gcp_vm.sh       # VM 자동배포
│  └─ lib/gcp_common.sh      # 공통 유틸
├─ docs/                     # 문서
│  ├─ quickstart.md
│  ├─ deploy.md
│  └─ ops.md
├─ .envexample               # 루트 예시 환경변수(자세한 설명 포함)
├─ Makefile                  # dev/lint/build/deploy 단축명령
└─ README.md
```

### CLI 빌드/설치 시 산출물
- pipx 또는 pip로 설치하면 `frvn` 명령이 시스템 PATH에 등록됩니다.
- `python -m build cli/`를 수행하면 `cli/dist/` 하위에 wheel(`.whl`)과 sdist(`.tar.gz`)가 생성됩니다.
- CLI 컨테이너 빌드 시 `frvn` 이 엔트리포인트로 포함된 이미지가 생성됩니다.

### `frvn init` 후 생성되는 프로젝트 구조(요약)

```text
myapp/
├─ backend/
│  ├─ app/                   # FastAPI 애플리케이션
│  ├─ nginx/                 # nginx.conf.template
│  ├─ supervisord.conf
│  ├─ docker-entrypoint.sh
│  └─ Dockerfile.backend     # 멀티스테이지 + Nginx + Supervisor
├─ frontend/
│  ├─ src/                   # React + Vite + Tailwind
│  ├─ index.html
│  └─ Dockerfile.frontend
├─ .envexample               # 환경변수 설명 포함(복사하여 .env 사용)
├─ docker-compose.dev.yml    # dev: backend(uvicorn --reload) + frontend(vite)
├─ docker-compose.prod.yml   # prod 유사 실행: backend(Nginx:8080), static(nginx)
└─ README.md                 # 프로젝트별 사용 가이드
```

### 빌드/배포 산출물
- 프론트엔드: `frontend/dist/` (Vite 빌드 결과) — GCS 버킷에 `gsutil rsync` 업로드
- 백엔드: Artifact Registry에 `${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${SERVICE_NAME}:${IMAGE_TAG}` 로 이미지 푸시
- Cloud Run 배포 시: `${SERVICE_NAME}` 서비스가 지정 리전에 생성, URL 발급
- VM 배포 시: `e2-*` 인스턴스 생성 및 startup-script로 Docker 설치/컨테이너 실행
- CDN/LB: GCS Backend Bucket 기반 HTTPS LB + Managed SSL(도메인 제공 시), Cloud CDN 활성화

## 템플릿으로 생성되는 구조

- backend: FastAPI, gunicorn/uvicorn, Nginx, supervisor
- frontend: React + Vite + Tailwind
- docker-compose.dev.yml: 백/프 dev 컨테이너
- docker-compose.prod.yml: 로컬 prod 유사 구동
- .envexample: 환경변수 템플릿

## 로컬 개발

```bash
cp .envexample .env
make dev           # 또는: docker compose -f docker-compose.dev.yml up -d --build
```

프런트: http://localhost:5173, 백엔드: http://localhost:8000, 헬스체크: /api/healthz

## 배포(GCP)

CLI를 통해 배포 스크립트를 프로젝트로 export 하거나, export+배포를 한번에 실행할 수 있습니다.

```bash
cp .envexample .env   # 또는 env.example -> .env
export $(grep -v '^#' .env | xargs) || true

# 1) export 후 수동 실행
frvn export deploy --to .
bash deploy/deploy_gcp_cloudrun.sh   # 또는: deploy/deploy_gcp_vm.sh

# 2) CLI가 export+실행을 한번에
frvn deploy cloudrun                 # 또는: frvn deploy vm
```

자세한 변수는 `.envexample` 확인.

## 배포 전략 선택 가이드

- 최소 복사(권장): `frvn init`은 앱 실행에 필요한 최소 파일만 생성합니다.
  - 배포가 필요할 때 `frvn export deploy`로 `deploy/`만 프로젝트에 추가
  - 또는 `frvn deploy cloudrun|vm`으로 export+실행을 한 번에 처리
- 항상 포함: 템플릿에 `deploy/`를 항상 포함하도록 바꿀 수도 있으나, 기본값은 깔끔한 구성을 위해 최소 복사입니다.
- 도메인/SSL: `FRONTEND_DOMAIN`을 지정하면 HTTPS LB + Managed SSL, CDN까지 자동 구성됩니다.

## 규칙/품질

- Python: Ruff(+Black), 기본 설정 제공
- JS/TS: ESLint(+Prettier), Tailwind 플러그인
- pre-commit: 포맷/린트 훅 제공

## 배포 패키징/배포 대안

- GitHub pipx 설치(권장): `pipx install git+https://github.com/quicklyorc/FRVN.git#subdirectory=cli`
- Dockerized CLI: `docker build -t frvn-cli -f cli/Dockerfile cli` 후 컨테이너로 실행
- GitHub 템플릿 리포지토리: 패키지 설치 없이 “Use this template”로 초기화


