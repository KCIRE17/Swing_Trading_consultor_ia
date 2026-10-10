@echo off
setlocal
cd /d "%~dp0"
title Swing Trading Consultor IA - Pruebas

rem ============================================================
rem  PRUEBAS - Swing Trading Consultor IA
rem
rem  Corre el smoke test (scripts\smoke.py), que valida:
rem    - indicadores sin NaN al serializar
rem    - ARIMA, backtest y motor de senales
rem    - modelo de sentimiento
rem    - endpoints HTTP con TestClient
rem
rem  No hace falta levantar el servidor: smoke.py usa
rem  fastapi.testclient contra la app en memoria.
rem
rem  Devuelve codigo 1 si alguna prueba falla, de modo que
rem  GitHub Actions pueda detectar el fallo.
rem ============================================================

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
    echo Las pruebas de Supabase y Gemini se omitiran y la app
    echo correra en modo fallback.
    echo.
)

echo.
echo ================================================
echo  SMOKE TEST
echo ================================================
echo.

".venv\Scripts\python.exe" scripts\smoke.py
set "CODIGO=%errorlevel%"

echo.
if "%CODIGO%"=="0" (
    echo ================================================
    echo  RESULTADO: todas las pruebas pasaron.
    echo ================================================
) else (
    echo ================================================
    echo  RESULTADO: hubo fallos. Revisa el detalle arriba.
    echo ================================================
)

pause
exit /b %CODIGO%
