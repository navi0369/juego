# 🎯 TRIVIA LAN - Guía Rápida de Inicio

## ⚡ Inicio Rápido

### 1. Iniciar el servidor
```bash
# Opción 1: Usar el script automático (Windows)
iniciar_servidor.bat

# Opción 2: Comando manual (con entorno virtual)
C:/proyect/.venv/Scripts/python.exe -m uvicorn server:asgi --host 0.0.0.0 --port 8000
```

### 2. Obtener tu IP LAN
```bash
# Windows
obtener_ip.bat
# o ejecutar: ipconfig

# Linux/Mac
hostname -I
```

### 3. Conectar jugadores
Los jugadores abren un navegador y van a:
```
http://TU-IP-LAN:8000
```
Ejemplo: `http://192.168.0.13:8000`

## 🎮 Cómo Jugar

1. **Primer jugador**: Se convierte automáticamente en HOST
2. **Otros jugadores**: Se unen a la misma sala
3. **HOST inicia**: Presiona "Iniciar Juego"
4. **Responder**: Escribir respuesta cuando aparece la pregunta
5. **Puntos**: 1º lugar = 3pts, 2º = 2pts, 3º = 1pt
6. **Ganar**: Primer jugador en llegar a 15 puntos

## 📁 Archivos Principales

- `server.py` - Servidor backend
- `static/client.html` - Interfaz web
- `data/items.csv` - Preguntas del juego
- `requirements.txt` - Dependencias Python

## ⚙️ Personalización

Edita `data/items.csv` para agregar tus propias preguntas:
```csv
id,tipo,texto,respuestas
21,deporte,"Deporte con raqueta y volante",Bádminton;Badminton
```

## 🔧 Solución de Problemas

### No se pueden conectar otros dispositivos
- Verifica que estén en la misma red WiFi
- Usa la IP LAN correcta (no 127.0.0.1)
- Desactiva temporalmente el firewall para probar

### Error de módulos
```bash
pip install -r requirements.txt
```

### Puerto ocupado
Cambia el puerto en el comando:
```bash
uvicorn server:asgi --host 0.0.0.0 --port 8001
```

## 🎯 Configuración Avanzada

Modifica variables en `server.py`:
- `TARGET_POINTS_DEFAULT = 15` (puntos para ganar)
- `ROUND_SECONDS = 30` (tiempo por ronda)
- `POINTS_BY_RANK = {1: 3, 2: 2, 3: 1}` (puntos por posición)

---

**¡Listo para jugar! 🎉**

Para soporte, revisa el `README.md` completo.
