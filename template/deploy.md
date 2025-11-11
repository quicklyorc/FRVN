# GCP 배포 가이드

이 문서는 템플릿에 포함된 `deploy/` 스크립트를 사용하여 GCP에 자동 배포하는 방법을 설명합니다.

## 사전 준비
- gcloud CLI 설치 및 인증
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```
- 프로젝트 선택/생성 및 설정
  ```bash
  gcloud projects create $PROJECT_ID || true
  gcloud config set project $PROJECT_ID
  ```
- 리소스/권한 활성화
  ```bash
  gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
  ```
- Artifact Registry 리포지토리(지역/포맷: docker) 생성
  ```bash
  gcloud artifacts repositories create $ARTIFACT_REPO --repository-format=docker --location=$REGION || true
  ```

## 환경변수 설정(.env)
프로젝트 루트의 `.envexample`을 `.env`로 복사하고 값들을 설정하세요.
```bash
cp .envexample .env
```
주요 변수:
- `PROJECT_ID`: GCP 프로젝트 ID
- `REGION`: 배포/레지스트리 지역 (예: asia-northeast3)
- `SERVICE_NAME`: Cloud Run 서비스명(컨테이너 이미지명 접두로도 사용)
- `ARTIFACT_REPO`: Artifact Registry 리포지토리명
- `IMAGE_TAG`: 컨테이너 이미지 태그 (latest 권장)

필요시 정적 자산/도메인 관련 변수도 설정할 수 있습니다. 변수 설명은 `.envexample` 내 주석을 참고하세요.

## 배포 실행
두 가지 방법이 있습니다.

### 1) frvn 명령어로 export+실행 한 번에
프로젝트 루트에서:
```bash
frvn deploy cloudrun   # Cloud Run 배포
# 또는
frvn deploy vm         # (옵션) GCE VM 배포
```
`deploy/` 스크립트가 자동으로 복사(export)되고, `.env`를 읽어 빌드/푸시/배포가 진행됩니다.

### 2) 스크립트 직접 실행
이미 `deploy/`가 있다면 다음처럼 직접 호출할 수 있습니다.
```bash
bash deploy/deploy_gcp_cloudrun.sh
# 또는
bash deploy/deploy_gcp_vm.sh
```

## 배포 결과 확인
Cloud Run:
```bash
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
```
표시된 URL로 접속하여 서비스 상태를 확인하세요.

## 문제 해결
- 권한/서비스 활성화 에러: 위의 서비스 활성화 명령을 재확인하고, IAM 권한(Artifact Registry, Cloud Run Admin 등)을 점검하세요.
- 이미지 푸시 실패: `gcloud auth configure-docker $REGION-docker.pkg.dev` 실행 후 재시도하세요.
- 환경변수 누락: `.env`를 재확인하고 누락된 값을 채우세요.


