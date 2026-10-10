@echo off
setlocal
cd /d "%~dp0"
title Swing Trading Consultor IA - Servidor local

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual. Ejecutando setup primero...
    echo.
    call setup.bat
    if errorlevel 1 exit /b 1
)

if exist "config.bat" (
    call config.bat
) else (
    echo.
    echo AVISO: no se encontro config.bat.
    echo La app correra en modo fallback:
    echo  - Precios en vivo desde Yahoo Finance (sin persistencia).
    echo  - Sin resumen IA de Gemini.
    echo.
)

echo.
echo ================================================
echo  Servidor:  http://localhost:8000
echo  API docs:  http://localhost:8000/docs
echo  Presiona Ctrl+C para detener.
echo ================================================
echo.
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000

echo.
echo El servidor se detuvo.
pause