@echo off
echo.
echo ===============================================
echo     🌐 OBTENER IP PARA TRIVIA LAN
echo ===============================================
echo.

echo Tu información de red:
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo 📍 IP encontrada:%%a
)

echo.
echo Los jugadores deben conectarse a:
echo http://TU-IP:8000
echo.
echo Ejemplo: http://192.168.1.100:8000
echo.

pause
