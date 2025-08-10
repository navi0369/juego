@echo off
echo.
echo ===============================================
echo     🎯 TRIVIA LAN - Servidor de Juego
echo ===============================================
echo.
echo Iniciando servidor...
echo.

cd /d "%~dp0"

REM Verificar si existe el entorno virtual
if not exist ".venv" (
    echo ❌ Error: No se encontró el entorno virtual
    echo Por favor ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activar entorno virtual e iniciar servidor
".venv\Scripts\python.exe" -c "from server import load_questions; preguntas = load_questions(); print(f'✅ {len(preguntas)} preguntas cargadas')"

echo.
echo 🚀 Iniciando servidor en http://0.0.0.0:8000
echo.
echo 📱 Los jugadores pueden conectarse desde:
echo    http://TU-IP-LAN:8000
echo.
echo Para obtener tu IP ejecuta: ipconfig
echo Busca la IPv4 de tu adaptador de red
echo.
echo ⏹️  Presiona Ctrl+C para detener el servidor
echo.

".venv\Scripts\python.exe" -m uvicorn server:asgi --host 0.0.0.0 --port 8000

pause
