"""
Configuración del juego Trivia LAN
Modifica estos valores para personalizar el juego
"""

# Configuración principal del juego
GAME_CONFIG = {
    # Puntos necesarios para ganar la partida
    "TARGET_POINTS_DEFAULT": 15,
    
    # Duración de cada ronda en segundos
    "ROUND_SECONDS": 30,
    
    # Puntos otorgados por posición en el podio
    "POINTS_BY_RANK": {
        1: 3,  # Primer lugar
        2: 2,  # Segundo lugar
        3: 1   # Tercer lugar
        # El resto obtiene 0 puntos
    },
    
    # Umbral de similitud para coincidencia difusa (0-100)
    "FUZZY_MATCH_THRESHOLD": 90,
    
    # Número máximo de jugadores por sala (0 = sin límite)
    "MAX_PLAYERS_PER_ROOM": 0,
    
    # Tiempo de espera antes de mostrar resultados (segundos)
    "RESULTS_DELAY": 2
}

# Configuración del servidor
SERVER_CONFIG = {
    # Puerto del servidor
    "PORT": 8000,
    
    # Host del servidor (0.0.0.0 para todas las interfaces)
    "HOST": "0.0.0.0",
    
    # Habilitar modo debug
    "DEBUG": False,
    
    # Habilitar recarga automática en desarrollo
    "RELOAD": False
}

# Configuración de archivos
FILES_CONFIG = {
    # Ruta al archivo CSV con preguntas
    "QUESTIONS_CSV": "data/items.csv",
    
    # Directorio de archivos estáticos
    "STATIC_DIR": "static",
    
    # Archivo HTML del cliente
    "CLIENT_HTML": "client.html"
}

# Mensajes del juego (para internacionalización)
MESSAGES = {
    "ROOM_NOT_FOUND": "Sala no encontrada",
    "PLAYER_NAME_IN_USE": "Nombre de jugador ya en uso",
    "ONLY_HOST_CAN_START": "Solo el host puede iniciar el juego",
    "GAME_ALREADY_STARTED": "El juego ya está iniciado",
    "NEED_MIN_PLAYERS": "Se necesita al menos 1 jugador",
    "NOT_IN_ROOM": "No estás en esta sala",
    "NO_ACTIVE_ROUND": "No hay ronda activa",
    "ANSWER_ALREADY_SUBMITTED": "Ya enviaste tu respuesta",
    "EMPTY_ANSWER": "La respuesta no puede estar vacía",
    "GAME_NOT_ACTIVE": "El juego no está activo",
    "ROUND_IN_PROGRESS": "Ya hay una ronda en curso"
}
