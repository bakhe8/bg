#!/usr/bin/env python3
"""
BGLApp Portable Launcher
"""
import os
import sys
import subprocess
import webbrowser
import time
import signal
import threading
from pathlib import Path

try:
    from update_portable import PortableUpdater
except ImportError:
    PortableUpdater = None


class BGLAppPortable:
    def __init__(self):
        self.launcher_dir = Path(__file__).resolve().parent
        self.base_dir = self.launcher_dir.parent
        self.app_dir = self.base_dir / 'app'
        self.main_dir = self.app_dir / 'main'
        self.runtime_dir = self.app_dir / 'portable_runtime'
        self.server_process = None
        self.is_running = True

    def setup_environment(self):
        python_paths = [
            str(self.runtime_dir),
            str(self.runtime_dir / 'Lib'),
            str(self.runtime_dir / 'Lib' / 'site-packages'),
            str(self.app_dir),
            str(self.main_dir),
        ]
        for path in python_paths:
            if path and path not in sys.path and Path(path).exists():
                sys.path.insert(0, path)
        os.environ['PYTHONPATH'] = os.pathsep.join(python_paths)
        os.environ.setdefault('BGLAPP_PORTABLE', '1')
        os.environ.setdefault('UVICORN_RELOAD', '0')
        os.environ.setdefault('PYTHONLEGACYWINDOWSDLLLOADING', '1')
        os.environ['PATH'] = os.pathsep.join([str(self.runtime_dir), os.environ.get('PATH', '')])
        self._maybe_apply_gtk_runtime()

    def find_python_executable(self):
        if sys.platform.startswith('win'):
            candidate = self.runtime_dir / 'python.exe'
        else:
            candidate = self.runtime_dir / 'bin' / 'python3'
        if candidate.exists():
            return str(candidate)
        return sys.executable

    def start_server(self):
        python_exe = self.find_python_executable()
        cmd = [python_exe, '-m', 'main.app']
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.app_dir,
        )
        threading.Thread(target=self._monitor_stdout, daemon=True).start()
        threading.Thread(target=self._monitor_stderr, daemon=True).start()

    def _monitor_stdout(self):
        if not self.server_process or not self.server_process.stdout:
            return
        for line in self.server_process.stdout:
            if not self.is_running:
                break;
            if line.strip():
                print(f"[SERVER] {line.rstrip()}")

    def _monitor_stderr(self):
        if not self.server_process or not self.server_process.stderr:
            return
        for line in self.server_process.stderr:
            if not self.is_running:
                break
            if line.strip():
                print(f"[ERROR] {line.rstrip()}")

    def open_browser(self):
        time.sleep(3)
        url = 'http://127.0.0.1:5000'
        try:
            webbrowser.open(url)
        except Exception as exc:  # noqa: BLE001
            print(f'⚠️ لا يمكن فتح المتصفح تلقائياً: {exc}')
            print(f'📍 افتح الرابط يدوياً: {url}')

    def signal_handler(self, *_):
        print('\n🛑 إيقاف BGLApp...')
        self.is_running = False
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
        sys.exit(0)

    def run(self):
        print('=' * 60)
        print('🎯 BGLApp Portable')
        print('=' * 60)
        auto_update = os.environ.get('BGLAPP_AUTO_UPDATE', '0') == '1'
        self.setup_environment()
        if auto_update and PortableUpdater:
            print('🔄 التحقق من وجود تحديثات...')
            PortableUpdater().run(auto=True)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        self.start_server()
        threading.Thread(target=self.open_browser, daemon=True).start()
        print('✅ يعمل الآن على http://127.0.0.1:5000')
        if self.server_process:
            self.server_process.wait()

    def _maybe_apply_gtk_runtime(self):
        hint_file = self.base_dir / "gtk_runtime_path.txt"
        if not hint_file.exists():
            return
        try:
            raw_value = hint_file.read_text(encoding='utf-8').strip()
        except OSError:
            return
        if not raw_value:
            return
        install_root = Path(raw_value)
        if not install_root.is_absolute():
            install_root = (self.base_dir / install_root).resolve()
        bin_dir = install_root / "bin"
        if bin_dir.exists():
            os.environ['PATH'] = os.pathsep.join([str(bin_dir), os.environ.get('PATH', '')])
            os.environ.setdefault('GTK_BASEPATH', str(install_root))

if __name__ == '__main__':
    BGLAppPortable().run()
