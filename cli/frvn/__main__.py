import argparse
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile


def print_err(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def render_text(text: str, replacements: dict[str, str]) -> str:
    for k, v in replacements.items():
        text = text.replace(f"{{{{{k}}}}}", v)
    return text


def copy_template(src: Path, dst: Path, replacements: dict[str, str]) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # Create directories
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)

    # Copy and render files
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            target = dst / rel
            if p.name == ".envexample":
                # Some environments block reading *.env* files; generate a safe default
                # Include descriptive comments for each variable to guide users.
                default_env = (
                    "# GCP 프로젝트 및 리전 설정\n"
                    "PROJECT_ID={{PROJECT_NAME}}-gcp\n"
                    "REGION=asia-northeast3\n"
                    "\n"
                    "# 서비스/이미지 관련 설정\n"
                    "# SERVICE_NAME: Cloud Run 서비스명 및 컨테이너 이미지명 접두로 사용\n"
                    "SERVICE_NAME={{SERVICE_NAME}}\n"
                    "# ARTIFACT_REPO: GCP Artifact Registry 리포지토리명 (사전 생성 필요)\n"
                    "ARTIFACT_REPO={{ARTIFACT_REPO}}\n"
                    "# IMAGE_TAG: 컨테이너 이미지 태그 (latest 권장, 배포마다 변경 가능)\n"
                    "IMAGE_TAG={{IMAGE_TAG}}\n"
                    "\n"
                    "# 정적 프런트엔드 자산 관련 설정(선택)\n"
                    "# FRONTEND_BUCKET: 정적 파일 호스팅 버킷명\n"
                    "FRONTEND_BUCKET={{SERVICE_NAME}}-bucket\n"
                    "# CACHE_TTL: CDN/캐시 TTL(초)\n"
                    "CACHE_TTL=3600\n"
                    "# CDN: 1이면 CDN 사용, 0이면 미사용\n"
                    "CDN=1\n"
                    "\n"
                    "# 커스텀 도메인(선택). 설정 시 배포 스크립트에서 참고만 합니다.\n"
                    "FRONTEND_DOMAIN=\n"
                    "BACKEND_DOMAIN=\n"
                    "ADMIN_EMAIL=\n"
                    "\n"
                    "# 로컬 개발용 백엔드 실행 포트 및 로그 설정\n"
                    "BACKEND_PORT=8000\n"
                    "UVICORN_WORKERS=1\n"
                    "GUNICORN_WORKERS=2\n"
                    "LOG_LEVEL=info\n"
                    "\n"
                    "# 로컬 도커 개발 편의용 UID/GID (퍼미션 이슈 방지)\n"
                    "DEV_UID=1000\n"
                    "DEV_GID=1000\n"
                )
                try:
                    target.write_text(render_text(default_env, replacements), encoding="utf-8")
                except PermissionError:
                    # Fallback filename when hidden .env-like files are blocked
                    alt = target.with_name("env.example")
                    alt.write_text(render_text(default_env, replacements), encoding="utf-8")
                continue
            try:
                text = p.read_text(encoding="utf-8")
                target.write_text(render_text(text, replacements), encoding="utf-8")
            except UnicodeDecodeError:
                data = p.read_bytes()
                target.write_bytes(data)
            except PermissionError as e:
                # Fallback: skip problematic files except envexample handled above
                raise e


def cmd_init(args: argparse.Namespace) -> int:
    here = Path(__file__).resolve().parent
    # 1) Prefer packaged resources: frvn/resources/template (installed wheel)
    packaged_template = here / "resources" / "template"
    if packaged_template.exists():
        template_dir = packaged_template
    else:
        # 2) Fallback for development: repo-root/template (when running from source tree)
        # here: .../FRVN/cli/frvn/__main__.py -> parents[2] = repo root (FRVN)
        template_dir = (here.parents[2] / "template").resolve()

    # Determine target directory:
    # - If destination provided (not "."), respect it with resolve()
    # - Otherwise, prefer $PWD (shell-reported CWD) if valid; fallback to os.getcwd()
    # Always generate into current working directory for simplicity
    target_dir = Path.cwd()

    project_name = args.name or target_dir.name
    service_name = args.service or project_name.replace("_", "-")

    replacements = {
        "PROJECT_NAME": project_name,
        "SERVICE_NAME": service_name,
        "ARTIFACT_REPO": args.artifact_repo or "frvn-repo",
        "IMAGE_TAG": args.image_tag or "latest",
    }

    print(f"Generating project into: {target_dir}")
    copy_template(template_dir, target_dir, replacements)
    # Also export deploy/ scripts into the project by default for convenience
    class _NS:  # simple namespace for reuse of export handler
        pass
    ns = _NS()
    ns.to = str(target_dir)
    ns.force = False
    cmd_export_deploy(ns)
    print("Done.")
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    import shutil as _sh

    tools = ["docker", "gcloud", "node", "npm", "python3"]
    missing = [t for t in tools if not _sh.which(t)]
    if missing:
        print_err("Missing tools: " + ", ".join(missing))
        return 1
    print("All required tools are available.")
    return 0


def _resource_path(*parts: str) -> Path:
    return Path(__file__).resolve().parent / "resources" / Path(*parts)


def cmd_export_deploy(args: argparse.Namespace) -> int:
    src = _resource_path("deploy")
    dst_root = Path(args.to).resolve()
    dst = dst_root / "deploy"
    if dst.exists():
        if not args.force:
            raise FileExistsError(f"{dst} already exists. Use --force to overwrite.")
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"Exported deploy scripts to: {dst}")
    return 0


def _load_env_file(project_root: Path) -> None:
    # best-effort: load .env or env.example into os.environ
    for name in [".env", "env.example"]:
        p = project_root / name
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    if not line or line.strip().startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
            except PermissionError:
                continue
            break


def cmd_deploy(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    if not args.no_export:
        # ensure deploy/ exists in project
        class _NS: pass
        ns = _NS()
        ns.to = str(project_root)
        ns.force = args.force_export
        cmd_export_deploy(ns)
    _load_env_file(project_root)

    script = "deploy_gcp_cloudrun.sh" if args.target == "cloudrun" else "deploy_gcp_vm.sh"
    script_path = project_root / "deploy" / script
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}. Run 'frvn export deploy' first.")

    print(f"Running: {script_path}")
    proc = subprocess.run(["bash", str(script_path)], cwd=str(project_root))
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="frvn", description="FRVN project initializer")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize a new project from template")
    p_init.add_argument("destination", nargs="?", default=".", help="Target directory (default: .)")
    p_init.add_argument("--name", help="Project name")
    p_init.add_argument("--service", help="Service name")
    p_init.add_argument("--artifact-repo", help="Artifact Registry repo name")
    p_init.add_argument("--image-tag", help="Default image tag")
    p_init.set_defaults(func=cmd_init)

    p_doc = sub.add_parser("doctor", help="Check local toolchain")
    p_doc.set_defaults(func=cmd_doctor)

    p_export = sub.add_parser("export", help="Export auxiliary assets into current project")
    p_export_sub = p_export.add_subparsers(dest="what", required=True)
    p_export_deploy = p_export_sub.add_parser("deploy", help="Export deploy/ scripts")
    p_export_deploy.add_argument("--to", default=".", help="Destination project root (default: .)")
    p_export_deploy.add_argument("--force", action="store_true", help="Overwrite if exists")
    p_export_deploy.set_defaults(func=cmd_export_deploy)

    p_deploy = sub.add_parser("deploy", help="Deploy using embedded scripts")
    p_deploy.add_argument("target", choices=["cloudrun", "vm"], help="Deployment target")
    p_deploy.add_argument("--project-root", default=".", help="Project root that has backend/frontend")
    p_deploy.add_argument("--no-export", action="store_true", help="Do not copy scripts into project")
    p_deploy.add_argument("--force-export", action="store_true", help="Overwrite deploy/ when exporting")
    p_deploy.set_defaults(func=cmd_deploy)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())


