#!/usr/bin/env python3
"""Build portable distribution for BGLApp."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
ROOT_SRC = Path(__file__).resolve().parents[1]
MAIN_SRC = ROOT_SRC / "main"
TRANSITION_SRC = ROOT_SRC / "transition"
REFACTOR_SRC = ROOT_SRC / "BGLApp_Refactor"
PORTABLE_MAIN = APP_DIR / "main"
PORTABLE_TRANSITION = APP_DIR / "transition"
PORTABLE_REFACTOR = APP_DIR / "BGLApp_Refactor"
PORTABLE_RUNTIME = APP_DIR / "portable_runtime"
PORTABLE_WEB = APP_DIR / "bg_ui"
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
LAUNCHER_DIR = BASE_DIR / "launcher"
PYTHON_VERSION = "3.11.8"


class PortableBuilder:
    def __init__(self) -> None:
        self.base_dir = BASE_DIR
        self.dist_dir = DIST_DIR
        self.build_dir = BUILD_DIR
        self.launcher_dir = LAUNCHER_DIR
        self.portable_dir = self.dist_dir / "BGLApp_Portable"
        self._gtk_source = None

    def clean_dirs(self) -> None:
        for directory in (self.dist_dir, self.build_dir):
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)
        if PORTABLE_RUNTIME.exists():
            shutil.rmtree(PORTABLE_RUNTIME)
        PORTABLE_RUNTIME.mkdir(parents=True, exist_ok=True)

    def setup_launcher_files(self) -> None:
        print("📁 إعداد ملفات التشغيل...")
        icon_script = self.launcher_dir / "create_icon.py"
        if icon_script.exists():
            subprocess.run([sys.executable, str(icon_script)], check=False)
        required = [
            "run_portable.py",
            "run_portable_nowindow.py",
            "run_portable.bat",
            "create_shortcut.vbs",
            "icon.ico",
        ]
        for file in required:
            path = self.launcher_dir / file
            if not path.exists():
                print(f"⚠️  ملف {file} غير موجود")

    def copy_project(self) -> None:
        if PORTABLE_MAIN.exists():
            shutil.rmtree(PORTABLE_MAIN)
        shutil.copytree(MAIN_SRC, PORTABLE_MAIN)
        if TRANSITION_SRC.exists():
            if PORTABLE_TRANSITION.exists():
                shutil.rmtree(PORTABLE_TRANSITION)
            shutil.copytree(TRANSITION_SRC, PORTABLE_TRANSITION)
        if REFACTOR_SRC.exists():
            if PORTABLE_REFACTOR.exists():
                shutil.rmtree(PORTABLE_REFACTOR)
            shutil.copytree(REFACTOR_SRC, PORTABLE_REFACTOR)
        source_web = MAIN_SRC / "bg_ui"
        if source_web.exists():
            if PORTABLE_WEB.exists():
                shutil.rmtree(PORTABLE_WEB)
            shutil.copytree(source_web, PORTABLE_WEB)

    def download_embedded_python(self) -> None:
        if not sys.platform.startswith("win"):
            print("📍 استخدام Python النظام (لا حاجة لمضمن).")
            return
        import urllib.request

        print("📥 تحميل Python المضمن...")
        url = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
        zip_path = self.build_dir / "python-embed.zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(PORTABLE_RUNTIME)
        print("✅ تم تجهيز Python المضمن")
        self.configure_embedded_python()
        self.bootstrap_pip()

    def bootstrap_pip(self) -> None:
        import urllib.request

        python_exe = PORTABLE_RUNTIME / ("python.exe" if os.name == "nt" else "bin/python3")
        get_pip = self.build_dir / "get-pip.py"
        if not get_pip.exists():
            url = "https://bootstrap.pypa.io/get-pip.py"
            urllib.request.urlretrieve(url, get_pip)
        subprocess.check_call([str(python_exe), str(get_pip)])

    def configure_embedded_python(self) -> None:
        major, minor, *_ = PYTHON_VERSION.split(".")
        pth_file = PORTABLE_RUNTIME / f"python{major}{minor}._pth"
        if not pth_file.exists():
            return
        lines = [line.strip() for line in pth_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        changed = False
        extra_entries = ["Lib", r"Lib\site-packages", "..", r"..\main"]
        for entry in extra_entries:
            if entry not in lines:
                lines.append(entry)
                changed = True
        new_lines = []
        for line in lines:
            if line.startswith("#import site"):
                new_lines.append("import site")
                changed = True
            else:
                new_lines.append(line)
        if changed:
            pth_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def install_requirements(self) -> None:
        requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
        if not requirements.exists():
            print("⚠️ لا يوجد ملف requirements.txt")
            return
        python_exe = PORTABLE_RUNTIME / ("python.exe" if os.name == "nt" else "bin/python3")
        target = PORTABLE_RUNTIME / "Lib" / "site-packages"
        target.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
        subprocess.check_call(
            [
                str(python_exe),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--target",
                str(target),
                "-r",
                str(requirements),
            ],
            env=env,
        )

    def build_with_pyinstaller(self) -> None:
        print("🔨 بناء النسخة العادية (console)...")
        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--icon",
            str(self.launcher_dir / "icon.ico"),
            "--name",
            "BGLApp",
            "--distpath",
            str(self.dist_dir),
            str(self.launcher_dir / "run_portable.py"),
        ])

    def build_noconsole_version(self) -> None:
        print("🔨 بناء النسخة الصامتة...")
        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--noconsole",
            "--icon",
            str(self.launcher_dir / "icon.ico"),
            "--name",
            "BGLApp_Silent",
            "--distpath",
            str(self.dist_dir),
            str(self.launcher_dir / "run_portable_nowindow.py"),
        ])

    def create_portable_package(self) -> None:
        if self.portable_dir.exists():
            shutil.rmtree(self.portable_dir)
        self.portable_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(APP_DIR, self.portable_dir / "app")
        shutil.copytree(self.launcher_dir, self.portable_dir / "launcher")
        gtk_hint = self.base_dir / "gtk_runtime_path.txt"
        if gtk_hint.exists():
            shutil.copy2(gtk_hint, self.portable_dir / "gtk_runtime_path.txt")
        for exe_name in ("BGLApp.exe", "BGLApp_Silent.exe"):
            exe_path = self.dist_dir / exe_name
            if exe_path.exists():
                shutil.copy2(exe_path, self.portable_dir / exe_name)

    def _find_gtk_runtime(self) -> Path | None:
        if self._gtk_source and self._gtk_source.exists():
            return self._gtk_source
        candidates: list[Path] = []
        hint_file = self.base_dir / "gtk_runtime_path.txt"
        if hint_file.exists():
            try:
                raw_path = hint_file.read_text(encoding="utf-8").strip()
                if raw_path:
                    candidates.append(Path(raw_path))
                    candidates.append((self.base_dir / raw_path).resolve())
            except OSError:
                pass
        env_hint = os.environ.get("GTK_RUNTIME_PATH") or os.environ.get("GTK_BASEPATH")
        if env_hint:
            candidates.append(Path(env_hint))
        default_locations = [
            Path(r"C:\Program Files\GTK3-Runtime Win64"),
            Path(r"C:\Program Files\GTK3-Runtime"),
            Path.home() / "AppData/Local/GTK3-Runtime",
        ]
        candidates.extend(default_locations)
        seen: set[Path] = set()
        for candidate in candidates:
            if not candidate:
                continue
            path = candidate.expanduser()
            if not path:
                continue
            resolved = path if path.is_absolute() else (self.base_dir / path).resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if (resolved / "bin" / "libgobject-2.0-0.dll").exists():
                self._gtk_source = resolved
                return resolved
        return None

    def bundle_gtk_runtime(self) -> None:
        source = self._find_gtk_runtime()
        if not source:
            print("⚠️  لم يتم العثور على GTK Runtime؛ سيستخدم المشغل الملف الخارجي إن وُجد.")
            return
        destination = self.portable_dir / "gtk_runtime"
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)
        copied = False
        for folder in ("bin", "lib", "etc", "share"):
            src_folder = source / folder
            if src_folder.exists():
                shutil.copytree(src_folder, destination / folder)
                copied = True
        if not copied:
            shutil.copytree(source, destination, dirs_exist_ok=True)
        hint_file = self.portable_dir / "gtk_runtime_path.txt"
        hint_file.write_text("gtk_runtime\n", encoding="utf-8")
        print(f"✅ تم تضمين GTK Runtime من {source}")

    def create_autorun_file(self) -> None:
        autorun_content = """[autorun]\nLabel=BGLApp Portable\nIcon=icon.ico\nOpen=run_portable.bat\nAction=تشغيل نظام خطابات الضمان\n"""
        (self.portable_dir / "autorun.inf").write_text(autorun_content, encoding="utf-8")

    def create_desktop_shortcut(self) -> None:
        if sys.platform != "win32":
            return
        script = self.launcher_dir / "create_shortcut.vbs"
        if not script.exists():
            return
        local_script = self.portable_dir / "create_shortcut.vbs"
        shutil.copy2(script, local_script)
        env = os.environ.copy()
        env["BGLAPP_SHORTCUT_SILENT"] = "1"
        subprocess.run(["wscript", str(local_script)], check=False, env=env)

    def build(self) -> None:
        print("🚀 بدء بناء الإصدار المحمول")
        print("=" * 50)
        try:
            self.clean_dirs()
            self.setup_launcher_files()
            self.download_embedded_python()
            self.install_requirements()
            self.copy_project()
            self.build_with_pyinstaller()
            self.build_noconsole_version()
            self.create_portable_package()
            self.bundle_gtk_runtime()
            self.create_autorun_file()
            self.create_desktop_shortcut()
            print("=" * 50)
            print("🎉 اكتمل بناء الإصدار المحمول بنجاح!")
            print(f"📍 الموقع: {self.portable_dir}")
        except Exception as exc:  # pragma: no cover
            print(f"❌ فشل البناء: {exc}")
            sys.exit(1)


def main() -> None:
    builder = PortableBuilder()
    builder.build()


if __name__ == "__main__":
    main()
