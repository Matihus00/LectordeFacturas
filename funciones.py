import fitz  # PyMuPDF
from dotenv import load_dotenv
import os
import pandas as pd
import pytesseract
from PIL import Image
import io
import sqlite3

# Cargar variables de entorno desde el archivo .env
load_dotenv(".env")

# Configurar pytesseract si no está en el PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
    raise FileNotFoundError("No se encontró Tesseract OCR en la ruta especificada. Verifica la instalación.")

def tiene_imagenes_pdf(ruta_pdf):
    """Verifica si un PDF contiene imágenes."""
    doc = fitz.open(ruta_pdf)
    return any(page.get_images(full=True) for page in doc)

def extraer_texto_pdf(ruta_pdf):
    """Extrae texto de un PDF y lo limpia."""
    doc = fitz.open(ruta_pdf)
    texto = "\n".join([page.get_text("text") for page in doc])
    return limpiar_texto(texto)

def extraer_texto_pdf_con_imagenes(ruta_pdf):
    """Extrae texto de un PDF que contiene imágenes usando OCR y lo limpia."""
    doc = fitz.open(ruta_pdf)
    texto_extraido = ""

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        images = page.get_images(full=True)

        for img in images:
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                texto_extraido += pytesseract.image_to_string(image) + "\n"
            except Exception as e:
                print(f"❌ Error al procesar una imagen en la página {page_num}: {e}")

    return limpiar_texto(texto_extraido)

def limpiar_texto(texto):
    """
    Limpia el texto eliminando caracteres no deseados, normalizando espacios,
    y corrigiendo errores comunes en los datos extraídos del OCR.
    """
    import re

    # Eliminar caracteres no deseados (incluyendo los nuevos símbolos especificados)
    texto = re.sub(r"[^\w\s.,;:/-]", "", texto)  # Mantiene solo caracteres alfanuméricos y algunos símbolos básicos
    texto = texto.replace("~", "").replace("“", "").replace("”", "").replace("™", "")
    texto = texto.replace("=", "").replace("*", "").replace("$", "").replace("@", "")
    texto = texto.replace("/", "").replace("«", "").replace("»", "")

    # Reemplazar múltiples espacios por un solo espacio
    texto = re.sub(r"\s+", " ", texto)

    # Normalizar separadores de miles y decimales
    texto = texto.replace(".", "").replace(",", ".")

    # Eliminar líneas vacías o con solo espacios
    lineas = [linea.strip() for linea in texto.split("\n") if linea.strip()]

    # Opcional: Corregir errores comunes en palabras clave
    texto_limpio = "\n".join(lineas)
    texto_limpio = texto_limpio.replace("prooveedor", "proveedor")
    texto_limpio = texto_limpio.replace("precio_unitarrio", "precio_unitario")

    return texto_limpio

def limpiar_csv(csv_texto):
    """Limpia el texto del CSV para corregir problemas de formato."""
    if not csv_texto.strip():
        print("⚠️ El CSV está vacío.")
        return ""

    lineas = csv_texto.split("\n")
    lineas_limpias = [linea.strip() for linea in lineas if linea.strip()]
    if lineas_limpias:
        lineas_limpias[0] = ";".join([
            col.strip()
               .replace("prooveedor","proveedor")
               .replace("precio_unitarrio", "precio_unitario")
               .lower()  # Fuerza minúsculas para evitar diferencias
            for col in lineas_limpias[0].split(";")
        ])
    return "\n".join(lineas_limpias)
    
def verificar_columnas(df, columnas_necesarias):
    """Verifica si las columnas necesarias existen en el DataFrame."""
    if df.empty:
        print("⚠️ El DataFrame está vacío.")
        return columnas_necesarias

    columnas_en_df = [col.strip().lower() for col in df.columns]
    return [col for col in columnas_necesarias if col.lower() not in columnas_en_df]

def crear_tabla_sqlite():
    """Crea la tabla SQLite para almacenar las facturas si no existe."""
    conn = sqlite3.connect('facturas.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cantidad INT,
        precio_unitario REAL,
        precio_total REAL,
        descripcion TEXT,
        fecha_factura DATE, 
        proveedor TEXT
    );
    """)
    conn.commit()
    conn.close()