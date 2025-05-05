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
                    if funciones.tiene_imagenes_pdf(ruta_archivo):
                        encabezado, productos_df = funciones.extraer_texto_pdf_con_imagenes(ruta_archivo)
                    else:
                        encabezado, productos_df = funciones.extraer_texto_pdf(ruta_archivo)

                    # Imprimir encabezado y productos para depuración
                    print("Encabezado:")
                    for key, value in encabezado.items():
                        print(f"{key}: {value}")

                    print("\nProductos:")
                    print(productos_df.to_string(index=False))

                    # Verificar si hay productos procesados
                    if productos_df.empty:
                        print(f"⚠️ No se encontraron productos en el archivo {archivo}.")
                        continue

                    # Agregar los productos al DataFrame general
                    facturas_dataframes.append(productos_df)

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
        if columna in ['cantidad','precio_unitario','precio_total']:
            df[columna] = pd.to_numeric(df[columna].astype(str).str.replace(",", "."), errors='coerce')
        elif columna == 'fecha_factura':
            df[columna] = pd.to_datetime(df[columna], errors='coerce')
        else:
            df[columna] = df[columna].astype(str)
    else:
        print(f"⚠️ La columna '{columna}' no existe en el DataFrame.")

df.fillna({'cantidad': 0,'precio_unitario': 0,'precio_total': 0,'descripcion':'Sin descripción', 'proveedor': 'Desconocido'}, inplace=True)

engine = create_engine("sqlite:///facturas.db")
try:
    df.to_sql("facturas", engine, if_exists="append", index=False)
    print("✅ Datos guardados en la base de datos.")
except Exception as e:
    print(f"❌ Error al guardar los datos en la base de datos: {e}")
engine.dispose()