#!/usr/bin/env python3
"""
Test simple para verificar que las correcciones funcionan
"""

import requests
import time

def test_server_health():
    try:
        response = requests.get("http://192.168.0.99:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor funcionando: {data['rooms']} salas, {data['questions']} preguntas")
            return True
        else:
            print(f"❌ Error en servidor: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Verificando servidor...")
    if test_server_health():
        print("🎉 Las correcciones están listas para probar manualmente")
        print("📋 Para probar:")
        print("1. Abre http://192.168.0.99:8000 en 2 navegadores")
        print("2. Únete a la misma sala")
        print("3. Inicia el juego")
        print("4. Responde correctamente para terminar ronda anticipadamente")
        print("5. Inicia siguiente ronda y verifica que:")
        print("   - No se repita la pregunta anterior")
        print("   - El tiempo comience desde 30 segundos")
        print("   - No termine inmediatamente")
    else:
        print("❌ El servidor no está funcionando")
