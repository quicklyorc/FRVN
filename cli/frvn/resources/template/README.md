{{PROJECT_NAME}} - FRVN 템플릿 기반 프로젝트

## 템플릿 구조
```
.
├─ backend/                 # FastAPI 백엔드 앱
│  ├─ app/                  # 애플리케이션 소스
│  │  ├─ core/              # 설정/로깅 등 공용 모듈
│  │  └─ main.py            # FastAPI 엔트리
│  ├─ nginx/                # Nginx 템플릿
│  ├─ requirements.txt      # Python 의존성
│  ├─ supervisord.conf      # 프로덕션 실행(uvicorn+nginx)
│  ├─ Dockerfile.backend    # 백엔드 이미지 빌드
│  └─ docker-entrypoint.sh  # Nginx 템플릿 렌더링 등
├─ frontend/                # React + Vite 프런트엔드
│  ├─ src/                  # 프런트 소스
│  ├─ index.html
│  ├─ Dockerfile.frontend   # 프런트 빌드/배포 컨테이너
│  ├─ vite.config.ts        # 개발 프록시(/api → backend:8000)
│  └─ tailwind.config.js
├─ deploy/                  # GCP 배포 스크립트(자동 복사됨)
├─ docker-compose.dev.yml   # 로컬 개발용
├─ docker-compose.prod.yml  # 프로덕션 유사 실행용
├─ .envexample              # 환경변수 템플릿(설명 포함)
├─ ruff.toml                # Python 린팅 설정
└─ README.md                # 이 파일
```

### 폴더별 운용 가이드
- backend
  - `app/`에 FastAPI 라우팅, 서비스 로직, 스키마 등을 구성합니다.
  - `core/`에는 설정(`pydantic-settings`), 로깅, 공용 유틸을 둡니다.
  - 컨테이너 빌드는 `Dockerfile.backend`, 실행은 `supervisord+nginx`를 사용합니다.
- frontend
  - `src/`에 UI 코드와 상태관리 로직을 둡니다.
  - 개발 시 Vite 프록시가 `/api` 요청을 `backend:8000`으로 전달합니다.
  - 프로덕션 정적 배포는 `Dockerfile.frontend`의 build 단계 아티팩트를 사용합니다.
- deploy
  - `deploy_gcp_cloudrun.sh`, `deploy_gcp_vm.sh` 등 자동 배포 스크립트가 있습니다.
  - 프로젝트 루트의 `.env` 값을 사용하며, 세부 내용은 `deploy.md`를 참고하세요.

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
프로젝트 루트의 `deploy.md`를 참고하세요. 일반적으로:
```bash
export PROJECT_ID=...
export REGION=...
export SERVICE_NAME={{SERVICE_NAME}}
export ARTIFACT_REPO={{ARTIFACT_REPO}}
export IMAGE_TAG={{IMAGE_TAG}}

# Cloud Run
frvn deploy cloudrun
# 또는 VM
frvn deploy vm
```


