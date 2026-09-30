@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Python 3.10 or newer is required. Install Python with Tcl/Tk support, then run again.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe (
 py -3 -m venv .venv
 if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -c "import PIL" >nul 2>nul
if errorlevel 1 (
 .venv\Scripts\python.exe -m pip install "Pillow>=10,<13"
 if errorlevel 1 goto fail
)
.venv\Scripts\python.exe app.py
if errorlevel 1 goto fail
exit /b 0
:fail
 echo Startup failed. Please send the error text for troubleshooting.
 pause
