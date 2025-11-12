#!/usr/bin/env python3
"""Silent launcher for BGLApp portable."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

try:
    from update_portable import PortableUpdater
except ImportError:  # pragma: no cover - optional
    PortableUpdater = None  # type: ignore


class SilentLauncher:
    def __init__(self) -> None:
        self.launcher_dir = Path(__file__).resolve().parent
        self.base_dir = self.launcher_dir.parent
        self.app_dir = self.base_dir / "app"
        self.main_dir = self.app_dir / "main"
        self.runtime_dir = self.app_dir / "portable_runtime"
        self.server_process: subprocess.Popen[str] | None = None
        self.is_running = True

    def hide_console(self) -> None:
        if sys.platform == "win32":  # pragma: no cover - platform specific
            try:
                import ctypes

                handle = ctypes.windll.kernel32.GetConsoleWindow()
                if handle:
                    ctypes.windll.user32.ShowWindow(handle, 0)
            except Exception:
                pass

    def setup_environment(self) -> None:
        python_paths = [
            str(self.runtime_dir),
            str(self.runtime_dir / "Lib"),
            str(self.runtime_dir / "Lib" / "site-packages"),
            str(self.app_dir),
            str(self.main_dir),
        ]
        for path in python_paths:
            if path and path not in sys.path and Path(path).exists():
                sys.path.insert(0, path)
        os.environ["PYTHONPATH"] = os.pathsep.join(python_paths)
        os.environ.setdefault("BGLAPP_PORTABLE", "1")
        os.environ.setdefault("UVICORN_RELOAD", "0")
        os.environ.setdefault("PYTHONLEGACYWINDOWSDLLLOADING", "1")
        os.environ["PATH"] = os.pathsep.join([str(self.runtime_dir), os.environ.get("PATH", "")])
        os.chdir(self.app_dir)
        self._maybe_apply_gtk_runtime()

    def find_python(self) -> str:
        candidate = self.runtime_dir / "python.exe"
        if candidate.exists():
            return str(candidate)
        candidate = self.runtime_dir / "bin" / "python3"
        if candidate.exists():
            return str(candidate)
        return sys.executable

    def start_server(self) -> bool:
        python_exe = self.find_python()
        creationflags = 0
        if sys.platform == "win32":  # pragma: no cover - Windows only
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.server_process = subprocess.Popen(
                [python_exe, "-m", "main.app"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags,
                cwd=self.app_dir,
            )
        except Exception as exc:
            self.show_error(f"تعذر تشغيل الخادم: {exc}")
            return False
        threading.Thread(target=self.monitor_output, daemon=True).start()
        return True

    def monitor_output(self) -> None:
        if not self.server_process:
            return
        stdout = self.server_process.stdout
        stderr = self.server_process.stderr
        while self.server_process and self.is_running:
            if stdout:
                line = stdout.readline()
                if line:
                    print(f"[SERVER] {line.rstrip()}")
            if stderr:
                line = stderr.readline()
                if line:
                    print(f"[ERROR] {line.rstrip()}")
            if self.server_process.poll() is not None:
                break

    def open_browser(self) -> None:
        time.sleep(3)
        try:
            webbrowser.open("http://127.0.0.1:5000")
        except Exception as exc:
            self.show_error(f"تعذر فتح المتصفح: {exc}")

    def show_error(self, message: str) -> None:
        if sys.platform == "win32":  # pragma: no cover
            try:
                import ctypes

                ctypes.windll.user32.MessageBoxW(0, message, "BGLApp Portable", 0x10)
                return
            except Exception:
                pass
        print(f"❌ {message}")

    def signal_handler(self, *_args) -> None:
        self.is_running = False
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except Exception:
                self.server_process.kill()

    def _maybe_apply_gtk_runtime(self) -> None:
        hint_file = self.base_dir / "gtk_runtime_path.txt"
        if not hint_file.exists():
            return
        try:
            raw_value = hint_file.read_text(encoding="utf-8").strip()
        except OSError:
            return
        if not raw_value:
            return
        install_root = Path(raw_value)
        if not install_root.is_absolute():
            install_root = (self.base_dir / install_root).resolve()
        bin_dir = install_root / "bin"
        if bin_dir.exists():
            os.environ["PATH"] = os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")])
            os.environ.setdefault("GTK_BASEPATH", str(install_root))

    def run(self) -> None:
        self.hide_console()
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        self.setup_environment()
        if os.environ.get("BGLAPP_AUTO_UPDATE") == "1" and PortableUpdater:
            PortableUpdater().run(auto=True)
        if not self.start_server():
            return
        threading.Thread(target=self.open_browser, daemon=True).start()
        if self.server_process:
            self.server_process.wait()
        self.signal_handler(None)


if __name__ == "__main__":
    SilentLauncher().run()
