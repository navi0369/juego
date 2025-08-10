# Ejemplo de uso del sistema de imágenes

Para usar el sistema con imágenes, sigue estos pasos:

## 1. Estructura de archivos
```
data/
├── items_images.csv      # Archivo CSV con preguntas de imagen
└── images/               # Carpeta con las imágenes locales
    ├── einstein.jpg
    ├── paris_tower.jpg
    ├── dolphin.jpg
    └── ...
```

## 2. Formato del CSV
El archivo items_images.csv debe tener estas columnas:
- id: Identificador único
- tipo: Categoría de la pregunta
- pregunta: Texto de la pregunta (ej: "¿Quién es esta persona?")
- imagen: Ruta a la imagen (local o URL)
- respuestas: Respuestas válidas separadas por ";"

## 3. Tipos de rutas de imagen:
- Local: "images/einstein.jpg" 
- URL: "https://example.com/image.jpg"

## 4. Compatibilidad
El sistema detecta automáticamente si usar:
- items_images.csv (con imágenes)
- items.csv (texto tradicional)

Si no encuentra items_images.csv, usará items.csv como respaldo.
