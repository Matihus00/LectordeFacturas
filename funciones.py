import fitz  # PyMuPDF
from dotenv import load_dotenv
import os
import pandas as pd
import re
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
    """Extrae texto de un PDF y lo envía a limpiar_texto."""
    doc = fitz.open(ruta_pdf)
    texto = "\n".join([page.get_text("text") for page in doc])
    return limpiar_texto(texto)  # Envía el texto extraído a limpiar_texto

def extraer_texto_pdf_con_imagenes(ruta_pdf):
    """Extrae texto de un PDF que contiene imágenes usando OCR y lo envía a limpiar_texto."""
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

    return limpiar_texto(texto_extraido)  # Envía el texto extraído a limpiar_texto

def limpiar_texto(texto):
    """
    Limpia el texto eliminando caracteres no deseados, normalizando espacios,
    y corrigiendo errores comunes en los datos extraídos del OCR.
    También estructura los datos en un encabezado y un DataFrame de productos,
    y envía el texto limpio a estructurar_texto.
    """
    import re
    import pandas as pd
    from Ollama_utils import estructurar_texto  # Importar la función para enviar a Ollama

    # Eliminar caracteres no deseados
    texto = re.sub(r"[^\w\s.,;:/-]", "", texto)
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

    # Estructurar los datos en encabezado y productos
    header_info = {}
    productos_section = []

    # Dividir el texto en encabezado y productos usando palabras clave
    if 'CODIGO CANTIDAD DESCRIPCION' in texto_limpio:
        header_text, productos_text = texto_limpio.split('CODIGO CANTIDAD DESCRIPCION', 1)
    elif 'Kiosco/Maxikiosco' in texto_limpio:
        header_text, productos_text = texto_limpio.split('Kiosco/Maxikiosco', 1)
    else:
        header_text = texto_limpio
        productos_text = ""

    # Procesar el encabezado
    header_text = header_text.strip()
    header_lines = header_text.split(',')
    for line in header_lines:
        if ':' in line:
            key_value = line.split(':', 1)
            key = key_value[0].strip()
            value = key_value[1].strip()
            header_info[key] = value

    # Patrón para extraer productos
    patron_productos = r'(\d+)\s+(.+?)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)%?\s+([\d.,]+)'

    # Limpiar caracteres especiales del texto de productos
    productos_text = productos_text.replace("~", "").replace("“", "").replace("”", "").replace("™", "")
    productos_text = productos_text.replace("=", "").replace("*", "").replace("$", "").replace("@", "")
    productos_text = productos_text.replace("/", "").replace("«", "").replace("»", "").strip()

    # Reemplazar formato de números (1.038,23 -> 1038.23)
    productos_text = re.sub(r'(\d+)\.(\d+),(\d+)', r'\1\2.\3', productos_text)

    # Buscar todos los productos en el texto
    matches = re.findall(patron_productos, productos_text)

    for match in matches:
        try:
            productos_section.append({
                'Cantidad': int(match[0]),
                'Descripción': match[1].strip(),
                'Precio': float(match[2].replace(',', '.')),
                'Imp_Int': float(match[3].replace(',', '.')),
                'IVA': float(match[4].replace(',', '.')),
                'Subtotal': float(match[5].replace(',', '.'))
            })
        except ValueError:
            continue

    # Crear un DataFrame con los productos
    productos_df = pd.DataFrame(productos_section)

    # Enviar el texto limpio a estructurar_texto
    try:
        respuesta_ollama = estructurar_texto(texto_limpio)
        print("✅ Respuesta de Ollama recibida.")
    except Exception as e:
        print(f"❌ Error al enviar el texto a Ollama: {e}")
        respuesta_ollama = None

    return header_info, productos_df, respuesta_ollama

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