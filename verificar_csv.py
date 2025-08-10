import pandas as pd
import os

print("🔍 Verificando archivo CSV...")

csv_path = "data/items.csv"
print(f"Buscando archivo: {os.path.abspath(csv_path)}")
print(f"¿Existe el archivo? {os.path.exists(csv_path)}")

if os.path.exists(csv_path):
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ CSV cargado exitosamente")
        print(f"Filas: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        
        # Mostrar primera pregunta
        if len(df) > 0:
            first_row = df.iloc[0]
            print(f"\nPrimera pregunta:")
            print(f"ID: {first_row['id']}")
            print(f"Tipo: {first_row['tipo']}")
            print(f"Texto: {first_row['texto']}")
            print(f"Respuestas: {first_row['respuestas']}")
        
    except Exception as e:
        print(f"❌ Error al leer CSV: {e}")
else:
    print("❌ Archivo CSV no encontrado")

print("\n🔍 Verificando directorio actual...")
print(f"Directorio actual: {os.getcwd()}")
print(f"Contenido del directorio:")
for item in os.listdir("."):
    print(f"  - {item}")
