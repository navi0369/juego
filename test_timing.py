#!/usr/bin/env python3
"""
Script de prueba automatizada para verificar los problemas de timing en las rondas
"""

import asyncio
import socketio
import time
import json

# Configuración de prueba
SERVER_URL = "http://192.168.0.99:8000"
ROOM_ID = "test_room"

class TestClient:
    def __init__(self, name):
        self.name = name
        self.sio = socketio.AsyncClient()
        self.current_question = None
        self.round_times = []
        self.questions_seen = []
        
        # Event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('room_joined', self.on_room_joined)
        self.sio.on('round_start', self.on_round_start)
        self.sio.on('round_end', self.on_round_end)
        self.sio.on('answer_correct', self.on_answer_correct)
        self.sio.on('error', self.on_error)
    
    async def connect(self):
        await self.sio.connect(SERVER_URL)
        await asyncio.sleep(0.5)
        
    async def join_room(self):
        await self.sio.emit('join_room', {
            'room_id': ROOM_ID,
            'player_name': self.name
        })
        await asyncio.sleep(0.5)
    
    async def start_game(self):
        await self.sio.emit('start_game', {'room_id': ROOM_ID})
        await asyncio.sleep(0.5)
    
    async def next_round(self):
        await self.sio.emit('next_round', {'room_id': ROOM_ID})
        await asyncio.sleep(0.5)
    
    async def submit_answer(self, answer):
        await self.sio.emit('submit_answer', {
            'room_id': ROOM_ID,
            'answer': answer
        })
    
    async def on_connect(self):
        print(f"[{self.name}] Conectado")
    
    async def on_room_joined(self, data):
        print(f"[{self.name}] Se unió a la sala - Host: {data.get('is_host', False)}")
    
    async def on_round_start(self, data):
        round_start_time = time.time()
        self.round_times.append(round_start_time)
        
        question_id = data.get('id')
        question_text = data.get('texto') or data.get('pregunta', 'Imagen')
        duration = data.get('duration')
        
        self.questions_seen.append(question_id)
        
        print(f"[{self.name}] Ronda iniciada - ID: {question_id}, Texto: {question_text[:50]}..., Duración: {duration}s")
        
        # Verificar si es una pregunta repetida
        if self.questions_seen.count(question_id) > 1:
            print(f"⚠️ [PROBLEMA] Pregunta repetida detectada - ID: {question_id}")
        
        self.current_question = data
        
        # Auto-responder para acelerar las pruebas
        if "gremlins" in question_text.lower() or question_id == 1001:
            await asyncio.sleep(1)  # Esperar un poco
            await self.submit_answer("Gremlins")
    
    async def on_round_end(self, data):
        round_end_time = time.time()
        
        if len(self.round_times) > 0:
            duration = round_end_time - self.round_times[-1]
            print(f"[{self.name}] Ronda terminada - Duración real: {duration:.2f}s")
            
            # Verificar si hay problemas de timing
            if duration < 5 and len(self.round_times) > 1:
                print(f"⚠️ [PROBLEMA] Ronda muy corta detectada: {duration:.2f}s")
    
    async def on_answer_correct(self, data):
        print(f"[{self.name}] ✓ Respuesta correcta: {data.get('answer')}")
    
    async def on_error(self, data):
        print(f"[{self.name}] ❌ Error: {data.get('message')}")
    
    async def disconnect(self):
        await self.sio.disconnect()

async def run_test():
    print("🧪 Iniciando pruebas automatizadas...")
    
    # Crear clientes de prueba
    host = TestClient("Host_Test")
    player2 = TestClient("Player2_Test")
    
    try:
        # Conectar clientes
        await host.connect()
        await player2.connect()
        
        # Unirse a la sala
        await host.join_room()
        await player2.join_room()
        
        print("📋 Iniciando juego...")
        await host.start_game()
        
        # Esperar a que termine la primera ronda
        await asyncio.sleep(35)
        
        print("📋 Iniciando segunda ronda...")
        await host.next_round()
        
        # Esperar a que termine la segunda ronda
        await asyncio.sleep(35)
        
        print("📋 Iniciando tercera ronda...")
        await host.next_round()
        
        # Esperar un poco más
        await asyncio.sleep(10)
        
        print("✅ Pruebas completadas")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
    
    finally:
        await host.disconnect()
        await player2.disconnect()

if __name__ == "__main__":
    asyncio.run(run_test())
