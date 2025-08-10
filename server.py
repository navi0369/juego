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
FIRST_CORRECT_POINTS = 3  # Puntos para el primero que acierta
OTHER_CORRECT_POINTS = 1  # Puntos para otros que aciertan
MAX_SUBMISSIONS_PER_SECOND = 5  # Límite antispam

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
app.mount("/images", StaticFiles(directory="data/images"), name="images")

# Integrar Socket.IO con FastAPI
asgi = socketio.ASGIApp(sio, app)


def load_questions() -> List[Dict]:
    """
    Carga las preguntas desde el archivo CSV (con soporte para imágenes)
    """
    questions = []
    csv_path = os.path.join("data", "items_images.csv")
    
    if not os.path.exists(csv_path):
        print(f"⚠️ Archivo {csv_path} no encontrado, intentando con items.csv...")
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
                'respuestas': respuestas
            }
            
            # Verificar si es formato con imágenes o texto
            if 'imagen' in df.columns:
                question['pregunta'] = str(row['pregunta'])
                question['imagen'] = str(row['imagen'])
                question['es_imagen'] = True
            else:
                question['texto'] = str(row['texto'])
                question['es_imagen'] = False
            
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
        "round_timer_task": None,  # Tarea asyncio para cancelar
        "target_points": TARGET_POINTS_DEFAULT,
        "round_answers": {},  # sid -> lista de respuestas con timestamps
        "round_correct_players": set(),  # jugadores que ya acertaron en esta ronda
        "player_submission_times": {},  # sid -> lista de timestamps para antispam
        "used_questions": set(),  # IDs de preguntas ya usadas
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


def get_random_question(used_questions: Set[int]) -> Optional[Dict]:
    """
    Obtiene una pregunta aleatoria que no haya sido usada
    """
    if not game_state["questions"]:
        return None
    
    # Filtrar preguntas no usadas
    available_questions = [q for q in game_state["questions"] if q["id"] not in used_questions]
    
    # Si no hay preguntas disponibles, reiniciar la lista
    if not available_questions:
        available_questions = game_state["questions"]
        used_questions.clear()
    
    return random.choice(available_questions)


async def start_round(room_id: str):
    """
    Inicia una nueva ronda en una sala
    """
    room = get_room(room_id)
    if not room or room["game_finished"]:
        return
    
    # Cancelar cualquier timer anterior
    if room["round_timer_task"] and not room["round_timer_task"].done():
        room["round_timer_task"].cancel()
    
    # Seleccionar pregunta aleatoria que no haya sido usada
    question = get_random_question(room["used_questions"])
    if not question:
        await sio.emit("error", {"message": "No hay preguntas disponibles"}, room=room_id)
        return
    
    # Marcar pregunta como usada
    room["used_questions"].add(question["id"])
    
    # Configurar ronda
    room["current_question"] = question
    room["round_start_time"] = time.time()
    room["round_answers"] = {}
    room["round_correct_players"] = set()
    room["player_submission_times"] = {}
    
    # Enviar pregunta a todos los jugadores
    question_data = {
        "id": question["id"],
        "tipo": question["tipo"],
        "duration": ROUND_SECONDS,
        "es_imagen": question.get("es_imagen", False)
    }
    
    # Agregar texto o imagen según el tipo de pregunta
    if question.get("es_imagen", False):
        question_data["pregunta"] = question["pregunta"]
        # Convertir ruta relativa a URL absoluta si es necesario
        imagen = question["imagen"]
        if not imagen.startswith("http"):
            question_data["imagen"] = f"/images/{imagen.replace('images/', '')}"
        else:
            question_data["imagen"] = imagen
    else:
        question_data["texto"] = question["texto"]
    
    await sio.emit("round_start", question_data, room=room_id)
    
    # Programar fin de ronda con una tarea que podamos cancelar
    room["round_timer_task"] = asyncio.create_task(schedule_round_end(room_id))


async def schedule_round_end(room_id: str):
    """
    Programa el fin de ronda después del tiempo límite
    """
    try:
        await asyncio.sleep(ROUND_SECONDS)
        room = get_room(room_id)
        if room and room["current_question"]:  # Solo terminar si la ronda sigue activa
            await end_round(room_id)
    except asyncio.CancelledError:
        # La tarea fue cancelada, esto es normal cuando la ronda termina anticipadamente
        pass


async def end_round(room_id: str):
    """
    Finaliza la ronda actual y calcula puntuaciones
    """
    room = get_room(room_id)
    if not room or not room["current_question"]:
        return
    
    # Cancelar el timer si está activo
    if room["round_timer_task"] and not room["round_timer_task"].done():
        room["round_timer_task"].cancel()
    
    question = room["current_question"]
    correct_answers = []
    
    # Procesar todas las respuestas de todos los jugadores
    for sid, answer_list in room["round_answers"].items():
        if sid in room["players"]:
            player_name = room["players"][sid]["name"]
            
            # Buscar la primera respuesta correcta de este jugador
            first_correct = None
            for answer_data in answer_list:
                user_answer = answer_data["answer"]
                is_correct = check_answer(user_answer, question["respuestas"])
                
                if is_correct:
                    first_correct = {
                        "sid": sid,
                        "name": player_name,
                        "answer": user_answer,
                        "timestamp": answer_data["timestamp"]
                    }
                    break
            
            if first_correct:
                correct_answers.append(first_correct)
    
    # Ordenar por timestamp (primero en responder correctamente)
    correct_answers.sort(key=lambda x: x["timestamp"])
    
    # Asignar puntos: 3 al primero, 1 a los demás
    round_results = []
    for i, answer in enumerate(correct_answers):
        sid = answer["sid"]
        is_first = (i == 0)
        points = FIRST_CORRECT_POINTS if is_first else OTHER_CORRECT_POINTS
        
        room["players"][sid]["score"] += points
        
        round_results.append({
            "rank": i + 1,
            "name": answer["name"],
            "answer": answer["answer"],
            "points": points,
            "is_first": is_first
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
            "respuestas_correctas": question["respuestas"]
        },
        "results": round_results,
        "scores": {player["name"]: player["score"] for player in room["players"].values()},
        "game_finished": room["game_finished"],
        "winner": winner
    }
    
    # Agregar texto o pregunta según el tipo
    if question.get("es_imagen", False):
        round_end_data["question"]["pregunta"] = question["pregunta"]
    else:
        round_end_data["question"]["texto"] = question["texto"]
    
    # Enviar resultados
    await sio.emit("round_end", round_end_data, room=room_id)
    
    # Limpiar estado de ronda
    room["current_question"] = None
    room["round_start_time"] = None
    room["round_answers"] = {}
    room["round_correct_players"] = set()
    room["player_submission_times"] = {}
    room["round_timer_task"] = None


def is_rate_limited(room: Dict, sid: str) -> bool:
    """
    Verifica si un jugador está enviando demasiadas respuestas (antispam)
    """
    current_time = time.time()
    
    if sid not in room["player_submission_times"]:
        room["player_submission_times"][sid] = []
    
    # Filtrar timestamps de la última segundo
    recent_submissions = [
        t for t in room["player_submission_times"][sid]
        if current_time - t < 1.0
    ]
    
    room["player_submission_times"][sid] = recent_submissions
    
    return len(recent_submissions) >= MAX_SUBMISSIONS_PER_SECOND


async def check_round_completion(room_id: str):
    """
    Verifica si todos los jugadores han acertado para terminar la ronda anticipadamente
    """
    room = get_room(room_id)
    if not room or not room["current_question"]:
        return
    
    total_players = len(room["players"])
    correct_players = len(room["round_correct_players"])
    
    # Si todos los jugadores han acertado, terminar la ronda
    if correct_players >= total_players:
        await end_round(room_id)
@app.get("/")
async def root():
    """
    Redirige a la interfaz del cliente
    """
    return FileResponse("static/client.html")
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
        
        # Reiniciar puntuaciones y lista de preguntas usadas
        for player in room["players"].values():
            player["score"] = 0
        room["used_questions"] = set()  # Resetear preguntas usadas
        
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
    Procesa la respuesta de un jugador - permite múltiples intentos
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
        
        # Verificar si el jugador ya acertó en esta ronda
        if sid in room["round_correct_players"]:
            await sio.emit("error", {"message": "Ya acertaste en esta ronda"}, room=sid)
            return
        
        # Verificar límite de spam
        if is_rate_limited(room, sid):
            await sio.emit("error", {"message": "Enviando respuestas muy rápido, espera un momento"}, room=sid)
            return
        
        if not answer:
            await sio.emit("error", {"message": "La respuesta no puede estar vacía"}, room=sid)
            return
        
        # Registrar timestamp de envío para antispam
        current_time = time.time()
        if sid not in room["player_submission_times"]:
            room["player_submission_times"][sid] = []
        room["player_submission_times"][sid].append(current_time)
        
        # Inicializar lista de respuestas si no existe
        if sid not in room["round_answers"]:
            room["round_answers"][sid] = []
        
        # Agregar nueva respuesta
        answer_data = {
            "answer": answer,
            "timestamp": current_time
        }
        room["round_answers"][sid].append(answer_data)
        
        player_name = room["players"][sid]["name"]
        
        # Verificar si la respuesta es correcta
        is_correct = check_answer(answer, room["current_question"]["respuestas"])
        
        if is_correct:
            # Marcar jugador como que ya acertó
            room["round_correct_players"].add(sid)
            
            # Confirmar respuesta correcta
            await sio.emit("answer_correct", {"answer": answer}, room=sid)
            
            # Notificar a otros que alguien acertó
            await sio.emit("player_got_correct", {"name": player_name}, room=room_id)
            
            # Verificar si todos han acertado para terminar la ronda
            await check_round_completion(room_id)
        else:
            # Confirmar recepción de respuesta incorrecta
            await sio.emit("answer_incorrect", {"answer": answer}, room=sid)
        
        # Notificar a otros que alguien respondió (sin revelar si es correcta)
        await sio.emit("player_answered", {"name": player_name}, room=room_id)
        
        print(f"📝 {player_name} respondió: {answer} ({'✓' if is_correct else '✗'})")
        
    except Exception as e:
        print(f"❌ Error en submit_answer: {e}")
        await sio.emit("error", {"message": "Error al enviar respuesta"}, room=sid)


# Cargar preguntas al inicializar (fuera del if __name__)
print("🚀 Cargando preguntas del sistema...")
game_state["questions"] = load_questions()
if not game_state["questions"]:
    print("⚠️ ADVERTENCIA: No se pudieron cargar preguntas. Verifica data/items.csv")
else:
    print(f"✅ Sistema listo con {len(game_state['questions'])} preguntas")


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
