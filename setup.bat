@echo off
setlocal
cd /d "%~dp0"
title Setup - Swing Trading Consultor IA

echo ================================================
echo  Setup - Swing Trading Consultor IA
echo ================================================
echo.

set "PY="
where python >nul 2>nul
if not errorlevel 1 (
    set "PY=python"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PY=py"
    ) else (
        echo ERROR: Python no fue encontrado.
        echo.
        echo 1. Descarga e instala Python 3.12 o superior desde:
        echo    https://www.python.org/downloads/
        echo 2. En el instalador marca la casilla "Add python.exe to PATH".
        echo 3. Cierra y abre esta terminal de nuevo y ejecuta setup.bat.
        echo.
        pause
        exit /b 1
    )
)
echo Python detectado: %PY%

rem --- Validar version >= 3.12 ---
set "py_minor="
for /f "tokens=2 delims=." %%v in ('%PY% --version 2^>^&1') do set "py_minor=%%v"
if not defined py_minor (
    echo ERROR: No se pudo detectar la version de Python.
    pause
    exit /b 1
)
echo Version de Python detectada: 3.%py_minor%
if %py_minor% LSS 12 (
    echo ERROR: Se requiere Python 3.12 o superior. Version detectada: 3.%py_minor%
    pause
    exit /b 1
)

rem --- Crear el entorno virtual si no existe ---
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creando entorno virtual (.venv)...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR al crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo.
    echo Entorno virtual ya existe (.venv).
)

rem --- Instalar dependencias ---
echo.
echo Instalando dependencias (pyproject.toml)...
echo Puede tardar varios minutos y necesita internet.
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo.
    echo ERROR al instalar dependencias. Revisa tu conexion a internet.
    pause
    exit /b 1
)

rem --- Opcional: reentrenar el modelo de sentimiento ---
echo.
choice /c SN /m "Reentrenar el modelo de sentimiento? (opcional, requiere internet)"
if errorlevel 2 goto :done
echo.
echo Reentrenando modelo de sentimiento...
".venv\Scripts\python.exe" scripts\train_sentiment.py

:done
echo.
echo ================================================
echo  SETUP COMPLETADO
echo  Siguiente paso:
echo    1. Edita config.bat con tus credenciales.
echo    2. Ejecuta run.bat para iniciar la app.
echo ================================================
pause