"""Build a Windows portable distribution. Run with the build venv Python."""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.22.2'
DATA = ('cco_catalog.json', 'component_options.json', 'layout_options.json',
        'state_catalog.json', 'user_property_catalog.json', 'en.json')

def main():
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64') or sys.maxsize <= 2**32:
        raise SystemExit('Build requires Windows x64 and 64-bit Python. No executable was created.')
    for name in DATA:
        json.loads((ROOT / name).read_text(encoding='utf-8'))
    import tkinter
    import PIL
    import PyInstaller
    out = ROOT / 'exe_version_package'
    work = out / '_build_work'
    out.mkdir(exist_ok=True)
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
           '--onedir', '--windowed', '--name', 'TWUI_Studio',
           '--paths', str(ROOT), '--distpath', str(out),
           '--workpath', str(work), '--specpath', str(work),
           '--version-file', str(ROOT / 'packaging' / 'version_info.txt')]
    for name in DATA + ('examples',):
        cmd += ['--add-data', str(ROOT / name) + ';' + name if name == 'examples' else str(ROOT / name) + ';.']
    cmd.append(str(ROOT / 'packaging' / 'launcher.py'))
    subprocess.run(cmd, cwd=ROOT, check=True)
    folder = out / 'TWUI_Studio'
    exe = folder / 'TWUI_Studio.exe'
    with exe.open('rb') as f:
        if f.read(2) != b'MZ':
            raise RuntimeError('Expected Windows PE executable')
    # Verify the actual frozen app can load Tk, catalogs and construct its UI.
    subprocess.run([str(exe), '--smoke-test'], cwd=folder, check=True, timeout=90)
    for name in ('README_KO.md', 'README_EN.md', 'LICENSE.txt', 'THIRD_PARTY_NOTICES.txt', 'CHANGELOG.md'):
        shutil.copy2(ROOT / name, folder / name)
    shutil.copy2(ROOT / 'packaging' / 'PORTABLE_README.txt', folder / 'START_HERE.txt')
    (folder / 'VERSION.txt').write_text(VERSION + '\n', encoding='utf-8')
    (folder / 'BUILD_INFO.txt').write_text(
        f'Python {sys.version}\nPyInstaller {PyInstaller.__version__}\nPillow {PIL.__version__}\n', encoding='utf-8')
    # Preserve notices for the bundled Python interpreter and packages.
    from importlib.metadata import distribution
    licenses = folder / 'licenses'
    licenses.mkdir(exist_ok=True)
    for package in ('Pillow', 'PyInstaller'):
        dist = distribution(package)
        for file in dist.files or ():
            if any(word in str(file).lower() for word in ('license', 'copying', 'notice')) and Path(dist.locate_file(file)).is_file():
                target = licenses / package / str(file)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dist.locate_file(file), target)
    for file in (Path(sys.base_prefix) / 'LICENSE.txt', Path(sys.base_prefix) / 'LICENSE'):
        if file.exists():
            shutil.copy2(file, licenses / 'Python-LICENSE.txt')
            break
    archive = out / f'TWUI_Studio_{VERSION}_Windows_x64.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for file in sorted(folder.rglob('*')):
            if file.is_file():
                z.write(file, file.relative_to(out))
    print(f'Build and startup check passed: {archive}')
    print(f'Run: {exe}')
    print('Distribute the Windows_x64.zip above; _build_work is temporary build output.')

if __name__ == '__main__':
    main()
