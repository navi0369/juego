"""
Servidor de Trivia Multijugador LAN
Backend usando FastAPI + python-socketio
"""

import asyncio
import csv
import json
import os
import random
import time
import unicodedata
from typing import Dict, List, Optional, Set

import pandas as pd
import socketio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from rapidfuzz import fuzz

# Configuración del juego
TARGET_POINTS_DEFAULT = 15  # Puntos necesarios para ganar
ROUND_SECONDS = 30  # Duración de cada ronda en segundos
POINTS_BY_RANK = {1: 3, 2: 2, 3: 1}  # Puntos por posición en el podio

# Estado global del juego
game_state = {
    "rooms": {},  # room_id -> room_data
    "questions": [],  # Lista de preguntas cargadas del CSV
}

# Configuración de Socket.IO
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")

# Configuración de FastAPI
app = FastAPI(title="Trivia LAN Game Server")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Integrar Socket.IO con FastAPI
asgi = socketio.ASGIApp(sio, app)


def load_questions() -> List[Dict]:
    """
    Carga las preguntas desde el archivo CSV
    """
    questions = []
    csv_path = os.path.join("data", "items.csv")
    
    if not os.path.exists(csv_path):
        print(f"⚠️ Archivo {csv_path} no encontrado")
        return questions
    
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            # Dividir respuestas por punto y coma
            respuestas = [resp.strip() for resp in str(row['respuestas']).split(';')]
            
            question = {
                'id': int(row['id']),
                'tipo': str(row['tipo']),
                'texto': str(row['texto']),
                'respuestas': respuestas
            }
            questions.append(question)
        
        print(f"✅ Cargadas {len(questions)} preguntas desde {csv_path}")
        
    except Exception as e:
        print(f"❌ Error al cargar preguntas: {e}")
    
    return questions


def normalize_text(text: str) -> str:
    """
    Normaliza texto eliminando tildes y convirtiendo a minúsculas
    """
    # Remover tildes
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    # Convertir a minúsculas y eliminar espacios extra
    return text.lower().strip()


def check_answer(user_answer: str, correct_answers: List[str]) -> bool:
    """
    Verifica si la respuesta del usuario es correcta usando coincidencia difusa
    """
    user_normalized = normalize_text(user_answer)
    
    for correct in correct_answers:
        correct_normalized = normalize_text(correct)
        
        # Coincidencia exacta
        if user_normalized == correct_normalized:
            return True
        
        # Coincidencia difusa con umbral del 90%
        similarity = fuzz.ratio(user_normalized, correct_normalized)
        if similarity >= 90:
            return True
    
    return False


def create_room(room_id: str, host_sid: str) -> Dict:
    """
    Crea una nueva sala de juego
    """
    room_data = {
        "id": room_id,
        "host": host_sid,
        "players": {},  # sid -> player_data
        "game_started": False,
        "current_question": None,
        "round_start_time": None,
        "round_timer": None,
        "target_points": TARGET_POINTS_DEFAULT,
        "round_answers": {},  # sid -> respuesta y timestamp
        "game_finished": False,
        "winner": None
    }
    
    game_state["rooms"][room_id] = room_data
    return room_data


def get_room(room_id: str) -> Optional[Dict]:
    """
    Obtiene los datos de una sala
    """
    return game_state["rooms"].get(room_id)


def add_player_to_room(room_id: str, sid: str, player_name: str) -> bool:
    """
    Agrega un jugador a una sala
    """
    room = get_room(room_id)
    if not room:
        return False
    
    # Verificar que el nombre no esté en uso
    for player_data in room["players"].values():
        if player_data["name"].lower() == player_name.lower():
            return False
    
    room["players"][sid] = {
        "name": player_name,
        "score": 0,
        "connected": True
    }
    
    return True


def remove_player_from_room(room_id: str, sid: str):
    """
    Elimina un jugador de una sala
    """
    room = get_room(room_id)
    if not room:
        return
    
    if sid in room["players"]:
        del room["players"][sid]
    
    # Si era el host, asignar nuevo host o eliminar sala
    if room["host"] == sid:
        if room["players"]:
            # Asignar nuevo host al primer jugador
            room["host"] = list(room["players"].keys())[0]
        else:
            # Eliminar sala vacía
            del game_state["rooms"][room_id]


def get_random_question() -> Optional[Dict]:
    """
    Obtiene una pregunta aleatoria
    """
    if not game_state["questions"]:
        return None
    
    return random.choice(game_state["questions"])


async def start_round(room_id: str):
    """
    Inicia una nueva ronda en una sala
    """
    room = get_room(room_id)
    if not room or room["game_finished"]:
        return
    
    # Seleccionar pregunta aleatoria
    question = get_random_question()
    if not question:
        await sio.emit("error", {"message": "No hay preguntas disponibles"}, room=room_id)
        return
    
    # Configurar ronda
    room["current_question"] = question
    room["round_start_time"] = time.time()
    room["round_answers"] = {}
    
    # Enviar pregunta a todos los jugadores
    question_data = {
        "id": question["id"],
        "tipo": question["tipo"],
        "texto": question["texto"],
        "duration": ROUND_SECONDS
    }
    
    await sio.emit("round_start", question_data, room=room_id)
    
    # Programar fin de ronda
    await asyncio.sleep(ROUND_SECONDS)
    await end_round(room_id)


async def end_round(room_id: str):
    """
    Finaliza la ronda actual y calcula puntuaciones
    """
    room = get_room(room_id)
    if not room or not room["current_question"]:
        return
    
    question = room["current_question"]
    correct_answers = []
    
    # Procesar respuestas y determinar ganadores
    for sid, answer_data in room["round_answers"].items():
        if sid in room["players"]:
            user_answer = answer_data["answer"]
            is_correct = check_answer(user_answer, question["respuestas"])
            
            if is_correct:
                correct_answers.append({
                    "sid": sid,
                    "name": room["players"][sid]["name"],
                    "answer": user_answer,
                    "timestamp": answer_data["timestamp"]
                })
    
    # Ordenar por timestamp (primero en responder)
    correct_answers.sort(key=lambda x: x["timestamp"])
    
    # Asignar puntos
    round_results = []
    for i, answer in enumerate(correct_answers):
        sid = answer["sid"]
        rank = i + 1
        points = POINTS_BY_RANK.get(rank, 0)
        
        if points > 0:
            room["players"][sid]["score"] += points
        
        round_results.append({
            "rank": rank,
            "name": answer["name"],
            "answer": answer["answer"],
            "points": points
        })
    
    # Verificar si alguien ganó
    winner = None
    for sid, player_data in room["players"].items():
        if player_data["score"] >= room["target_points"]:
            winner = player_data["name"]
            room["game_finished"] = True
            room["winner"] = winner
            break
    
    # Preparar datos del resultado
    round_end_data = {
        "question": {
            "texto": question["texto"],
            "respuestas_correctas": question["respuestas"]
        },
        "results": round_results,
        "scores": {player["name"]: player["score"] for player in room["players"].values()},
        "game_finished": room["game_finished"],
        "winner": winner
    }
    
    # Enviar resultados
    await sio.emit("round_end", round_end_data, room=room_id)
    
    # Limpiar estado de ronda
    room["current_question"] = None
    room["round_start_time"] = None
    room["round_answers"] = {}


@app.get("/")
async def root():
    """
    Redirige a la interfaz del cliente
    """
    return FileResponse("static/client.html")


@app.get("/health")
async def health():
    """
    Endpoint de salud
    """
    return {"status": "ok", "rooms": len(game_state["rooms"]), "questions": len(game_state["questions"])}


@sio.event
async def connect(sid, environ):
    """
    Maneja conexiones de Socket.IO
    """
    print(f"🔌 Cliente conectado: {sid}")


@sio.event
async def disconnect(sid):
    """
    Maneja desconexiones de Socket.IO
    """
    print(f"🔌 Cliente desconectado: {sid}")
    
    # Remover jugador de todas las salas
    for room_id in list(game_state["rooms"].keys()):
        room = get_room(room_id)
        if room and sid in room["players"]:
            player_name = room["players"][sid]["name"]
            remove_player_from_room(room_id, sid)
            
            # Notificar a otros jugadores
            await sio.emit("player_left", {"name": player_name}, room=room_id)
            await sio.emit("players_update", 
                         {"players": list(room["players"].values())}, 
                         room=room_id)


@sio.event
async def join_room(sid, data):
    """
    Maneja solicitudes para unirse a una sala
    """
    try:
        room_id = data.get("room_id", "").strip()
        player_name = data.get("player_name", "").strip()
        
        if not room_id or not player_name:
            await sio.emit("error", {"message": "Nombre de sala y jugador requeridos"}, room=sid)
            return
        
        # Crear sala si no existe
        room = get_room(room_id)
        if not room:
            room = create_room(room_id, sid)
        
        # Intentar agregar jugador
        if not add_player_to_room(room_id, sid, player_name):
            await sio.emit("error", {"message": "Nombre de jugador ya en uso"}, room=sid)
            return
        
        # Unir jugador a la sala de Socket.IO
        await sio.enter_room(sid, room_id)
        
        # Determinar si es el host
        is_host = (room["host"] == sid)
        
        # Confirmar unión
        await sio.emit("room_joined", {
            "room_id": room_id,
            "player_name": player_name,
            "is_host": is_host,
            "game_started": room["game_started"]
        }, room=sid)
        
        # Notificar a otros jugadores
        await sio.emit("player_joined", {"name": player_name}, room=room_id)
        await sio.emit("players_update", 
                     {"players": list(room["players"].values())}, 
                     room=room_id)
        
        print(f"👤 {player_name} se unió a la sala {room_id}")
        
    except Exception as e:
        print(f"❌ Error en join_room: {e}")
        await sio.emit("error", {"message": "Error al unirse a la sala"}, room=sid)


@sio.event
async def start_game(sid, data):
    """
    Inicia el juego (solo el host puede hacerlo)
    """
    try:
        room_id = data.get("room_id")
        room = get_room(room_id)
        
        if not room:
            await sio.emit("error", {"message": "Sala no encontrada"}, room=sid)
            return
        
        if room["host"] != sid:
            await sio.emit("error", {"message": "Solo el host puede iniciar el juego"}, room=sid)
            return
        
        if len(room["players"]) < 1:
            await sio.emit("error", {"message": "Se necesita al menos 1 jugador"}, room=sid)
            return
        
        if room["game_started"]:
            await sio.emit("error", {"message": "El juego ya está iniciado"}, room=sid)
            return
        
        # Iniciar juego
        room["game_started"] = True
        room["game_finished"] = False
        room["winner"] = None
        
        # Reiniciar puntuaciones
        for player in room["players"].values():
            player["score"] = 0
        
        await sio.emit("game_started", {}, room=room_id)
        
        # Iniciar primera ronda
        await start_round(room_id)
        
        print(f"🎮 Juego iniciado en sala {room_id}")
        
    except Exception as e:
        print(f"❌ Error en start_game: {e}")
        await sio.emit("error", {"message": "Error al iniciar el juego"}, room=sid)


@sio.event
async def next_round(sid, data):
    """
    Inicia la siguiente ronda (solo el host puede hacerlo)
    """
    try:
        room_id = data.get("room_id")
        room = get_room(room_id)
        
        if not room:
            await sio.emit("error", {"message": "Sala no encontrada"}, room=sid)
            return
        
        if room["host"] != sid:
            await sio.emit("error", {"message": "Solo el host puede iniciar rondas"}, room=sid)
            return
        
        if not room["game_started"] or room["game_finished"]:
            await sio.emit("error", {"message": "El juego no está activo"}, room=sid)
            return
        
        if room["current_question"]:
            await sio.emit("error", {"message": "Ya hay una ronda en curso"}, room=sid)
            return
        
        # Iniciar nueva ronda
        await start_round(room_id)
        
    except Exception as e:
        print(f"❌ Error en next_round: {e}")
        await sio.emit("error", {"message": "Error al iniciar ronda"}, room=sid)


@sio.event
async def submit_answer(sid, data):
    """
    Procesa la respuesta de un jugador
    """
    try:
        room_id = data.get("room_id")
        answer = data.get("answer", "").strip()
        
        room = get_room(room_id)
        if not room:
            await sio.emit("error", {"message": "Sala no encontrada"}, room=sid)
            return
        
        if sid not in room["players"]:
            await sio.emit("error", {"message": "No estás en esta sala"}, room=sid)
            return
        
        if not room["current_question"]:
            await sio.emit("error", {"message": "No hay ronda activa"}, room=sid)
            return
        
        if sid in room["round_answers"]:
            await sio.emit("error", {"message": "Ya enviaste tu respuesta"}, room=sid)
            return
        
        if not answer:
            await sio.emit("error", {"message": "La respuesta no puede estar vacía"}, room=sid)
            return
        
        # Registrar respuesta con timestamp
        room["round_answers"][sid] = {
            "answer": answer,
            "timestamp": time.time()
        }
        
        player_name = room["players"][sid]["name"]
        
        # Confirmar recepción
        await sio.emit("answer_submitted", {"answer": answer}, room=sid)
        
        # Notificar a otros que alguien respondió (sin revelar la respuesta)
        await sio.emit("player_answered", {"name": player_name}, room=room_id)
        
        print(f"📝 {player_name} respondió: {answer}")
        
    except Exception as e:
        print(f"❌ Error en submit_answer: {e}")
        await sio.emit("error", {"message": "Error al enviar respuesta"}, room=sid)


# Inicializar servidor
if __name__ == "__main__":
    # Cargar preguntas al inicio
    game_state["questions"] = load_questions()
    
    if not game_state["questions"]:
        print("⚠️ No se pudieron cargar preguntas. Verifica el archivo data/items.csv")
    
    print("🚀 Iniciando servidor...")
    print("📡 Conecta desde el navegador a: http://IP-LAN:8000/")
    
    import uvicorn
    uvicorn.run("server:asgi", host="0.0.0.0", port=8000, reload=True)
