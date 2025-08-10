# 🎯 Trivia LAN - Juego Multijugador

Un juego de trivia multijugador para redes locales (LAN) desarrollado con Python (FastAPI + Socket.IO) y JavaScript.

## 📋 Características

- **Multijugador en tiempo real**: Varios jugadores pueden unirse desde diferentes navegadores
- **Red local (LAN)**: No requiere conexión a internet una vez configurado
- **Preguntas personalizables**: Carga preguntas desde archivo CSV
- **Sistema de puntuación**: Puntos por velocidad de respuesta (1°=3pts, 2°=2pts, 3°=1pt)
- **Validación inteligente**: Coincidencia exacta y difusa de respuestas
- **Interfaz responsive**: Compatible con dispositivos móviles y escritorio

## 🚀 Instalación

### 1. Requisitos previos
- Python 3.8 o superior
- Navegador web moderno

### 2. Descargar e instalar dependencias

```bash
# Navegar al directorio del proyecto
cd trivia-lan

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar preguntas (Opcional)
El archivo `data/items.csv` contiene preguntas de ejemplo. Puedes editarlo siguiendo el formato:

```csv
id,tipo,texto,respuestas
1,persona,"Economista boliviano autor de 'La potencia plebeya'",Zavaleta;René Zavaleta
2,lugar,"Departamento de Bolivia cuya capital es Sucre",Chuquisaca
```

**Formato del CSV:**
- `id`: Número único de la pregunta
- `tipo`: Categoría (persona, lugar, película, etc.)
- `texto`: La pregunta o pista
- `respuestas`: Respuestas correctas separadas por punto y coma (;)

## 🎮 Cómo usar

### 1. Iniciar el servidor
```bash
uvicorn server:asgi --host 0.0.0.0 --port 8000
```

### 2. Obtener la IP de la PC anfitriona
**En Windows (PowerShell):**
```powershell
ipconfig
```
Busca la dirección IPv4 de tu adaptador de red local (generalmente empieza con 192.168.x.x o 10.x.x.x)

**En Linux/Mac:**
```bash
hostname -I
```

### 3. Conectar jugadores
Los jugadores deben abrir un navegador y navegar a:
```
http://IP-DE-LA-PC-ANFITRIONA:8000
```

Ejemplo: `http://192.168.1.100:8000`

### 4. Jugar
1. **Unirse**: Cada jugador elige un nombre y se une a la misma sala
2. **Iniciar**: El host (primer jugador) inicia el juego
3. **Responder**: Los jugadores escriben sus respuestas cuando aparece la pregunta
4. **Puntuación**: Se otorgan puntos según el orden de respuestas correctas
5. **Ganar**: El primer jugador en alcanzar 15 puntos gana

## ⚙️ Configuración

Puedes modificar estas variables en `server.py`:

```python
TARGET_POINTS_DEFAULT = 15  # Puntos para ganar
ROUND_SECONDS = 30  # Duración de cada ronda
POINTS_BY_RANK = {1: 3, 2: 2, 3: 1}  # Puntos por posición
```

## 🛠️ Estructura del proyecto

```
trivia-lan/
├── server.py              # Servidor backend (FastAPI + Socket.IO)
├── static/
│   └── client.html        # Interfaz del cliente (HTML + CSS + JS)
├── data/
│   └── items.csv         # Preguntas del juego
├── requirements.txt       # Dependencias de Python
└── README.md             # Este archivo
```

## 🔧 Solución de problemas

### Error: "No se puede conectar al servidor"
- Verifica que el servidor esté ejecutándose
- Asegúrate de usar la IP correcta de la PC anfitriona
- Verifica que no hay firewall bloqueando el puerto 8000

### Error: "Import could not be resolved"
- Instala las dependencias: `pip install -r requirements.txt`
- Verifica que estás usando Python 3.8 o superior

### No aparecen preguntas
- Verifica que el archivo `data/items.csv` existe y tiene el formato correcto
- Revisa la consola del servidor para mensajes de error

### Los jugadores no pueden conectarse desde otros dispositivos
- Verifica que todos los dispositivos están en la misma red
- Usa la IP LAN de la PC anfitriona (no 127.0.0.1 o localhost)
- Temporalmente deshabilita el firewall para probar

## 🎯 Mecánica del juego

### Puntuación
- **1er lugar**: 3 puntos
- **2do lugar**: 2 puntos  
- **3er lugar**: 1 punto
- **Resto**: 0 puntos

### Validación de respuestas
- Coincidencia exacta (ignorando mayúsculas/minúsculas)
- Coincidencia difusa con 90% de similitud
- Ignorar tildes y caracteres especiales

### Roles
- **Host**: El primer jugador que se une a una sala
  - Puede iniciar el juego
  - Puede avanzar a la siguiente ronda
- **Jugadores**: Pueden responder preguntas y ver puntuaciones

## 🔒 Seguridad y privacidad

- El juego funciona completamente en red local
- No se envían datos a servidores externos
- No se almacena información personal
- Las salas se eliminan automáticamente cuando todos los jugadores se desconectan

## 📱 Compatibilidad

- **Navegadores**: Chrome, Firefox, Safari, Edge (versiones modernas)
- **Dispositivos**: PC, laptops, tablets, smartphones
- **Sistemas operativos**: Windows, macOS, Linux, iOS, Android

## 🤝 Contribuir

Este es un proyecto de código abierto. Puedes:
- Reportar bugs
- Sugerir nuevas características
- Agregar más preguntas al CSV
- Mejorar la interfaz

## 📄 Licencia

Proyecto de uso libre para fines educativos y de entretenimiento.

---

**¡Diviértete jugando Trivia LAN! 🎉**
