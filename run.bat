@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Swing Trading Consultor IA - Servidor local

echo ================================================
echo  Swing Trading Consultor IA - Servidor local
echo ================================================
echo.

rem ---------- [1/5] Entorno ----------
echo [1/5] Verificando entorno virtual...
if not exist ".venv\Scripts\python.exe" (
    echo     No existe .venv. Ejecutando setup.bat...
    echo.
    call setup.bat
    if errorlevel 1 goto :error
)
if not exist ".venv\Scripts\python.exe" (
    echo     ERROR: el entorno virtual no pudo crearse.
    goto :error
)
echo     OK.

rem ---------- [2/5] Configuracion ----------
echo [2/5] Cargando configuracion...
if exist "config.bat" (
    call config.bat
    echo     config.bat cargado ^(DATABASE_URL / Gemini^).
) else (
    echo     AVISO: no se encontro config.bat.
    echo     La app correra en modo fallback:
    echo       - Precios en vivo desde Yahoo Finance ^(sin persistencia^).
    echo       - Sin resumen IA de Gemini.
)

rem ---------- [3/5] Puerto 8000 ----------
echo [3/5] Liberando el puerto 8000 si esta en uso...
set "PORT_PID="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do set "PORT_PID=%%p"
if defined PORT_PID (
    echo     Puerto 8000 ocupado por PID !PORT_PID!. Cerrando ese proceso...
    taskkill /T /F /PID !PORT_PID! >nul 2>nul
    ping -n 2 127.0.0.1 >nul
) else (
    echo     Puerto libre.
)

rem ---------- [4/5] Arrancar servidor ----------
echo [4/5] Iniciando servidor en segundo plano...
start "SwingTradingIA-Server" /min ".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000

echo     Esperando a que responda /api/health ...
set "OK="
for /l %%i in (1,1,20) do (
    if not defined OK (
        curl -s -o nul --max-time 2 http://127.0.0.1:8000/api/health
        if not errorlevel 1 (
            set "OK=1"
        ) else (
            ping -n 2 127.0.0.1 >nul
        )
    )
)
if not defined OK (
    echo     ERROR: el servidor no respondio en /api/health.
    goto :error
)

rem ---------- [5/5] Listo ----------
echo [5/5] Servidor listo.
echo.
echo ================================================
echo  Dashboard : http://localhost:8000
echo  API docs  : http://localhost:8000/docs
echo ================================================
echo.

:menu
choice /c SN /m "Deseas terminar y cerrar el servidor? (S=si / N=no)"
if errorlevel 2 goto :keep
echo.
echo Deteniendo el servidor...
taskkill /FI "WINDOWTITLE eq SwingTradingIA-Server*" /T /F >nul 2>nul
echo Servidor detenido. Cerrando todo.
ping -n 2 127.0.0.1 >nul
exit /b 0

:keep
echo.
echo El servidor sigue activo en http://localhost:8000
echo Presiona ENTER para volver a preguntar ^(o deja esta ventana abierta^).
pause >nul
goto :menu

:error
echo.
echo *************************************************
echo  ERROR: revisa los mensajes de arriba.
echo *************************************************
echo.
pause
exit /b 1
