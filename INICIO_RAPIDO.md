# 🎯 TRIVIA LAN - Guía Rápida de Inicio

## ⚡ Inicio Rápido

### 1. Iniciar el servidor
```bash
# Opción 1: Usar el script automático (Windows)
iniciar_servidor.bat

# Opción 2: Comando manual (con entorno virtual)
C:/proyect/.venv/Scripts/python.exe -m uvicorn server:asgi --host 0.0.0.0 --port 8000

# 2.1: Comando manual para Linux (con entorno virtual)
./.venv/bin/python -m uvicorn server:asgi --host 0.0.0.0 --port 8000
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
#ejemplo
http://192.168.0.99:8000
```
Ejemplo: `http://192.168.0.13:8000`

## 🎮 Cómo Jugar

1. **Primer jugador**: Se convierte automáticamente en HOST
2. **Otros jugadores**: Se unen a la misma sala
3. **HOST inicia**: Presiona "Iniciar Juego"
4. **Responder**: Tienes 30 segundos para responder
5. **Múltiples intentos**: Puedes enviar varias respuestas hasta acertar
6. **Puntos**: Primer acierto = 3pts, otros aciertos = 1pt
7. **Bloqueo**: Una vez que aciertas, no puedes responder más en esa ronda
8. **Fin de ronda**: Termina cuando se acaba el tiempo (30s) o todos aciertan
9. **Ganar**: Primer jugador en llegar a 15 puntos

## 🎯 Reglas de Ronda

- **Duración**: 30 segundos fijos por ronda
- **Múltiples intentos**: Envía tantas respuestas como quieras hasta acertar
- **Puntuación**:
  - 🥇 Primer acierto: **3 puntos**
  - 🥈 Otros aciertos: **1 punto**
  - ❌ Sin acierto: **0 puntos**
- **Bloqueo**: Si aciertas, quedas bloqueado para esa ronda
- **Antispam**: Máximo 5 respuestas por segundo

## 📁 Archivos Principales

- `server.py` - Servidor backend
- `static/client.html` - Interfaz web
- `data/items.csv` - Preguntas de texto tradicionales
- `data/items_images.csv` - Preguntas con imágenes
- `data/images/` - Carpeta de imágenes locales
- `requirements.txt` - Dependencias Python

## ⚙️ Personalización

### Preguntas de Texto:
Edita `data/items.csv`:
```csv
id,tipo,texto,respuestas
21,deporte,"Deporte con raqueta y volante",Bádminton;Badminton
```

### Preguntas con Imágenes:
Edita `data/items_images.csv`:
```csv
id,tipo,pregunta,imagen,respuestas
1,persona,"¿Quién es esta persona?","images/einstein.jpg","Einstein;Albert Einstein"
2,lugar,"¿Qué lugar es este?","https://example.com/tower.jpg","París;Torre Eiffel"
```

**🖼️ El sistema detecta automáticamente si usar texto o imágenes**

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
- `FIRST_CORRECT_POINTS = 3` (puntos al primero que acierta)
- `OTHER_CORRECT_POINTS = 1` (puntos a otros que aciertan)
- `MAX_SUBMISSIONS_PER_SECOND = 5` (límite antispam)

---

**¡Listo para jugar! 🎉**

Para soporte, revisa el `README.md` completo.
