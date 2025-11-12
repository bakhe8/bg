from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]


def runserver(args):
    os.environ.setdefault("PORT", str(args.port))
    uvicorn.run(
        "BGLApp_Refactor.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def run_tests(_args):
    subprocess.check_call([sys.executable, "-m", "pytest", "BGLApp_Refactor/tests"], cwd=ROOT_DIR)


def build_portable(_args):
    script = ROOT_DIR / "BGLApp_Portable" / "build_portable.py"
    subprocess.check_call([sys.executable, str(script)], cwd=ROOT_DIR / "BGLApp_Portable")


def main():
    parser = argparse.ArgumentParser(description="BGLApp developer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the FastAPI server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=5000)
    serve.add_argument("--reload", action="store_true", help="Enable auto-reload")
    serve.set_defaults(func=runserver)

    test = subparsers.add_parser("test", help="Run the refactor test suite")
    test.set_defaults(func=run_tests)

    build = subparsers.add_parser("build-portable", help="Build the portable distribution")
    build.set_defaults(func=build_portable)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
