import funciones
import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from io import StringIO
from Ollama_utils import estructurar_texto  # Importar desde Ollama

# Crear la tabla SQLite si no existe
funciones.crear_tabla_sqlite()

# Ruta de la carpeta principal de facturas
ruta_principal = r"C:\Users\matia\OneDrive\Desktop\Facturas\facturas"

# Lista para almacenar los DataFrames de las facturas
facturas_dataframes = []

# Recorrer todas las carpetas dentro de la carpeta "facturas"
for carpeta in sorted(os.listdir(ruta_principal)):
    ruta_carpeta = os.path.join(ruta_principal, carpeta)

    if os.path.isdir(ruta_carpeta):
        print(f"📁 Procesando la carpeta: {ruta_carpeta}")

        for archivo in os.listdir(ruta_carpeta):
            ruta_archivo = os.path.join(ruta_carpeta, archivo)

            if archivo.lower().endswith(".pdf") and os.path.isfile(ruta_archivo):
                print(f"📄 Procesando factura PDF: {ruta_archivo}")

                try:
                    # Extraer texto del PDF
                    if funciones.tiene_imagenes_pdf(ruta_archivo):
                        texto_no_estructurado = funciones.extraer_texto_pdf_con_imagenes(ruta_archivo)
                    else:
                        texto_no_estructurado = funciones.extraer_texto_pdf(ruta_archivo)

                    # Usar estructurar_texto desde Ollama
                    csv_respuesta = estructurar_texto(texto_no_estructurado)

                    if not csv_respuesta:
                        print(f"⚠️ No se pudo procesar el archivo {archivo}.")
                        continue

                    try:
                        # Convertir la respuesta de Ollama en un DataFrame
                        df_factura = pd.read_csv(StringIO(csv_respuesta), delimiter=";", dtype=str)
                        df_factura.columns = df_factura.columns.str.strip().str.lower()
                        print("🧾 Columnas encontradas en el DataFrame:", df_factura.columns.tolist())

                        # Verificar columnas necesarias
                        columnas_necesarias = ['cantidad', 'precio_unitario', 'precio_total', 'descripcion', 'fecha_factura', 'proveedor']
                        columnas_faltantes = funciones.verificar_columnas(df_factura, columnas_necesarias)

                        if columnas_faltantes:
                            print(f"⚠️ Faltan las siguientes columnas en el DataFrame: {columnas_faltantes}")
                            continue

                        # Convertir columnas numéricas
                        for columna in ['cantidad', 'precio_unitario', 'precio_total']:
                            df_factura[columna] = pd.to_numeric(df_factura[columna].str.replace(",", "."), errors='coerce')

                        facturas_dataframes.append(df_factura)

                    except Exception as e:
                        print(f"❌ Error al convertir el CSV en DataFrame: {e}")
                        continue

                except Exception as e:
                    print(f"❌ Error procesando PDF {archivo}: {e}")

# Concatenar todos los DataFrames
if facturas_dataframes:
    df = pd.concat(facturas_dataframes, ignore_index=True)
    print(f"✅ Se procesaron {len(df)} facturas.")
else:
    print("⚠️ No se procesaron facturas.")
    sys.exit(0)

# Normalizar y guardar en la base de datos
columnas_a_normalizar = ['cantidad', 'precio_unitario', 'precio_total', 'fecha_factura', 'descripcion', 'proveedor']
for columna in columnas_a_normalizar:
    if columna in df.columns:
        if columna in ['cantidad', 'precio_unitario', 'precio_total']:
            df[columna] = pd.to_numeric(df[columna].astype(str).str.replace(",", "."), errors='coerce')
        elif columna == 'fecha_factura':
            df[columna] = pd.to_datetime(df[columna], errors='coerce')
        else:
            df[columna] = df[columna].astype(str)
    else:
        print(f"⚠️ La columna '{columna}' no existe en el DataFrame.")

# Rellenar valores faltantes
df.fillna({'cantidad': 0, 'precio_unitario': 0, 'precio_total': 0, 'descripcion': 'Sin descripción', 'proveedor': 'Desconocido'}, inplace=True)

# Guardar en la base de datos
engine = create_engine("sqlite:///facturas.db")
try:
    df.to_sql("facturas", engine, if_exists="append", index=False)
    print("✅ Datos guardados en la base de datos.")
except Exception as e:
    print(f"❌ Error al guardar los datos en la base de datos: {e}")
engine.dispose()