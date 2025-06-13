@echo off
title Gandiva - by Hume Nano
cd /d "%~dp0"

echo Checking Python installation...

python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Installing Python...
    echo Downloading Python installer...
    
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile 'python_installer.exe'"
    
    if exist python_installer.exe (
        echo Installing Python...
        python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
        del python_installer.exe
        echo Python installation complete. Please restart this script.
        pause
        exit
    ) else (
        echo Failed to download Python installer.
        echo Please install Python manually from python.org
        pause
        exit
    )
)

echo Python found. Checking dependencies...

if not exist ".installed" (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    
    if errorlevel 1 (
        echo Failed to install dependencies.
        echo Please check your internet connection and try again.
        pause
        exit
    )
    
    echo. > .installed
    echo Dependencies installed successfully.
)

echo Starting Gandiva...
python gandiva.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start Gandiva
    echo Please check the error messages above.
    echo.
    pause
)