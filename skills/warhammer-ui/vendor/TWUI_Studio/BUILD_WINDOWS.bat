@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto missing
if not exist exe_version_package mkdir exe_version_package
if not exist exe_version_package\_build_venv\Scripts\python.exe (
  py -3 -m venv exe_version_package\_build_venv
  if errorlevel 1 goto failed
)
exe_version_package\_build_venv\Scripts\python.exe -m pip install "PyInstaller==6.22.2" "Pillow>=10,<13"
if errorlevel 1 goto failed
exe_version_package\_build_venv\Scripts\python.exe packaging\build_windows.py
if errorlevel 1 goto failed
 echo Build complete. Open exe_version_package for TWUI_Studio_0.22.2_Windows_x64.zip.
pause
exit /b 0
:missing
 echo Install 64-bit Python 3.12 with Tcl/Tk and the Python launcher, then retry.
pause
exit /b 1
:failed
 echo Build failed. Please send the error text above. No verified release is available.
pause
exit /b 1
