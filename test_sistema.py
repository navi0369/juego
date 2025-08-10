"""
Pruebas básicas para el servidor de Trivia LAN
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import load_questions, normalize_text, check_answer

def test_load_questions():
    """Prueba la carga de preguntas desde CSV"""
    print("🧪 Probando carga de preguntas...")
    questions = load_questions()
    
    if questions:
        print(f"✅ Cargadas {len(questions)} preguntas")
        
        # Mostrar primera pregunta como ejemplo
        if len(questions) > 0:
            q = questions[0]
            print(f"   Ejemplo: {q['texto']}")
            print(f"   Respuestas: {q['respuestas']}")
        
        return True
    else:
        print("❌ No se pudieron cargar preguntas")
        return False

def test_normalize_text():
    """Prueba la normalización de texto"""
    print("\n🧪 Probando normalización de texto...")
    
    test_cases = [
        ("José María", "jose maria"),
        ("GARCÍA", "garcia"),
        ("Niño", "nino"),
        ("  ESPACIOS  ", "espacios")
    ]
    
    all_passed = True
    for original, expected in test_cases:
        result = normalize_text(original)
        if result == expected:
            print(f"✅ '{original}' -> '{result}'")
        else:
            print(f"❌ '{original}' -> '{result}' (esperado: '{expected}')")
            all_passed = False
    
    return all_passed

def test_check_answer():
    """Prueba la validación de respuestas"""
    print("\n🧪 Probando validación de respuestas...")
    
    correct_answers = ["Einstein", "Albert Einstein", "A. Einstein"]
    
    test_cases = [
        ("Einstein", True),
        ("albert einstein", True),
        ("EINSTEIN", True),
        ("einstein", True),
        ("Albert", False),
        ("Eisntein", True),  # Error tipográfico pero > 90% similar
        ("Newton", False),
        ("A Einstein", True),
        ("", False)
    ]
    
    all_passed = True
    for user_answer, expected in test_cases:
        result = check_answer(user_answer, correct_answers)
        if result == expected:
            print(f"✅ '{user_answer}' -> {result}")
        else:
            print(f"❌ '{user_answer}' -> {result} (esperado: {expected})")
            all_passed = False
    
    return all_passed

def test_csv_format():
    """Verifica el formato del archivo CSV"""
    print("\n🧪 Probando formato del CSV...")
    
    csv_path = "data/items.csv"
    if not os.path.exists(csv_path):
        print(f"❌ Archivo {csv_path} no encontrado")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        required_columns = ['id', 'tipo', 'texto', 'respuestas']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Columnas faltantes: {missing_columns}")
            return False
        
        print(f"✅ CSV válido con {len(df)} filas")
        print(f"   Columnas: {list(df.columns)}")
        
        # Verificar que hay datos
        if len(df) == 0:
            print("⚠️ El CSV está vacío")
            return False
        
        # Verificar algunos tipos
        tipos_unicos = df['tipo'].unique()
        print(f"   Tipos de preguntas: {list(tipos_unicos)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al leer CSV: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas del sistema Trivia LAN")
    print("=" * 50)
    
    tests = [
        test_csv_format,
        test_load_questions,
        test_normalize_text,
        test_check_answer
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print("❌ Prueba falló")
        except Exception as e:
            print(f"💥 Error en prueba: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa la configuración.")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Sistema validado correctamente")
        print("🎮 Puedes ejecutar: uvicorn server:asgi --host 0.0.0.0 --port 8000")
    else:
        print("\n❌ Se encontraron problemas. Revisa los errores arriba.")
    
    input("\nPresiona Enter para salir...")
