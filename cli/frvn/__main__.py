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
    if dst.exists():
        # ensure clean destination to avoid permission/metadata issues
        shutil.rmtree(dst)

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
                default_env = (
                    "PROJECT_ID={{PROJECT_NAME}}-gcp\n"
                    "REGION=asia-northeast3\n"
                    "SERVICE_NAME={{SERVICE_NAME}}\n"
                    "ARTIFACT_REPO={{ARTIFACT_REPO}}\n"
                    "IMAGE_TAG={{IMAGE_TAG}}\n"
                    "\n"
                    "FRONTEND_BUCKET={{SERVICE_NAME}}-bucket\n"
                    "CACHE_TTL=3600\n"
                    "CDN=1\n"
                    "\n"
                    "FRONTEND_DOMAIN=\n"
                    "BACKEND_DOMAIN=\n"
                    "ADMIN_EMAIL=\n"
                    "\n"
                    "BACKEND_PORT=8000\n"
                    "UVICORN_WORKERS=1\n"
                    "GUNICORN_WORKERS=2\n"
                    "LOG_LEVEL=info\n"
                    "\n"
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
    template_dir = (here.parents[1] / "template").resolve()

    target_dir = Path(args.destination).resolve()
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
    p_init.add_argument("destination", help="Target directory")
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


