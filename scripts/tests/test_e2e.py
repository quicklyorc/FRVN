#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def assert_exists(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Missing expected path: {path}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    dest_root = repo_root / "__e2e__"
    project_dir = dest_root / "myapp"

    if project_dir.exists():
        shutil.rmtree(project_dir)
    dest_root.mkdir(parents=True, exist_ok=True)

    # Invoke CLI without installing package, using module path
    print(":: Generating project via CLI ...")
    cmd = [
        sys.executable,
        "-m",
        "cli.frvn.__main__",
        "init",
        str(project_dir),
        "--name",
        "myapp",
        "--service",
        "myapp",
        "--artifact-repo",
        "frvn-repo",
        "--image-tag",
        "test",
    ]
    res = run(cmd, cwd=repo_root)
    print(res.stdout)

    # Basic structure checks
    env_file = project_dir / ".envexample"
    if not env_file.exists():
        env_file = project_dir / "env.example"
    assert_exists(env_file)
    assert_exists(project_dir / "docker-compose.dev.yml")
    assert_exists(project_dir / "docker-compose.prod.yml")

    assert_exists(project_dir / "backend" / "app" / "main.py")
    assert_exists(project_dir / "backend" / "Dockerfile.backend")
    assert_exists(project_dir / "backend" / "nginx" / "nginx.conf.template")
    assert_exists(project_dir / "backend" / "supervisord.conf")

    assert_exists(project_dir / "frontend" / "src" / "App.tsx")
    assert_exists(project_dir / "frontend" / "vite.config.ts")
    assert_exists(project_dir / "frontend" / "Dockerfile.frontend")

    # Placeholder replacement check
    env_content = env_file.read_text(encoding="utf-8")
    if "{{" in env_content or "}}" in env_content:
        raise AssertionError("Placeholder replacement appears incomplete in .envexample")

    # docker-compose content sanity check
    dc = (project_dir / "docker-compose.dev.yml").read_text(encoding="utf-8")
    if "backend:" not in dc or "frontend:" not in dc:
        raise AssertionError("docker-compose.dev.yml seems malformed (missing services)")

    print(":: E2E basic scaffold test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


