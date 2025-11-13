import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app' / 'gui' / 'review_window.py'

if not APP.exists():
    raise SystemExit(f'لم يتم العثور على الملف: {APP}')


def main():
    subprocess.run([
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'BGL_Lite',
        '--hidden-import=webview',
        '--hidden-import=webview.platforms.edgechromium',
        '--add-data', 'app/templates;app/templates',
        '--add-data', 'app/config;app/config',
        str(APP),
    ], check=True)


if __name__ == '__main__':
    main()
