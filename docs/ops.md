운영 가이드

- 로그: gunicorn/uvicorn은 stdout, nginx는 stdout/stderr로 출력됩니다(컨테이너 로그로 수집).
- 롤백: Artifact Registry에 태그로 이미지가 보관됩니다. 이전 태그로 재배포하세요.
- 스케일링(Cloud Run): min/max 인스턴스, 동시성을 조절하세요.
- 스케일링(VM): 머신 타입/수평 확장(매니지드 인스턴스 그룹) 구성 고려.

보안/네트워킹

- Cloud Run는 기본적으로 HTTPS 엔드포인트를 제공합니다.
- VM의 TLS는 도메인/인증서 설정이 필요합니다(본 템플릿은 컨테이너 내부 Nginx를 기본 가정).


