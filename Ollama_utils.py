import requests
import json
from funciones import limpiar_csv

def estructurar_texto(texto):
    """Envía el texto a Ollama con el modelo phi3:medium y obtiene la respuesta estructurada en CSV."""
    try:
        prompt = """
        🎯 Eres un asistente experto en estructurar datos de facturas.Ordena los datos recibidos teniendo en cuenta que son facturas de compras de un negocio

        Tu tarea es **convertir el texto de una factura en una tabla CSV**, usando **punto y coma (;)** como separador. Sigue estrictamente las instrucciones y no incluyas explicaciones, encabezados duplicados ni texto adicional.

        ⚠️ **Instrucciones importantes:**
        1. Devuelve solo los datos solicitados en el siguiente orden, con una única línea de encabezado:
           
fecha_factura;proveedor;cantidad;precio_unitario;precio_total;descripcion

        2. Cada línea debe representar un producto individual de la factura.
        3. No incluyas líneas vacías, encabezados repetidos ni comentarios adicionales.

        🧾 **Definición de campos:**
        1. **fecha_factura**: Fecha de emisión de la factura en formato dd/mm/aaaa.
           - Si no está explícita, usa la fecha más cercana al texto de la factura.
        2. **proveedor**: Nombre del proveedor.
           - Si no aparece claro, deja el campo vacío.
        3. **cantidad**: Número entero de unidades.
           - Sin decimales ni texto adicional.
           - Si el valor es mayor a 999, coloca 0.
           - Si no está explícito, calcula dividiendo precio_total entre precio_unitario.
        4. **precio_unitario**: Precio por unidad.
           - Usa **coma como separador decimal**.
           - Sin separador de miles ni símbolos monetarios.
           - Usa el valor que diga "unitario","neto" o "Precio".
        5. **precio_total**: Total del producto.
           - Usa **coma como separador decimal**.
           - Sin separador de miles ni símbolos monetarios.
           - Usa el valor que diga "Total" o "Subtotal".
        6. **descripcion**: Descripción completa del producto.
           - No la resumas ni generes paréntesis, observaciones o comentarios.

        🚫 **No permitidos:**
        - Valores como nan, null, N/A o cualquier otro valor falso.
        - No Repetición del encabezado.
        - No Comentarios, explicaciones, notas, fórmulas o marcas de formato.
        - N0 comentarios, en inglés o español.
        - precio_unitario y precio_total no deben tener separador de miles corrige si es necesario.
        ✅ **Ejemplo esperado:**
        
fecha_factura;proveedor;cantidad;precio_unitario;precio_total;descripcion
        06/12/2024;DTS SRL;3;860,00;2580,00;Papas Lays Clásicas 40g x68
        06/12/2024;DTS SRL;5;490,50;2452,50;Cheetos Queso 43g x 40


        📌 **Texto a procesar:**
        {texto.strip()}
        """
        print(f"🔍 Texto enviado a Ollama:\n{texto.strip()}")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3:medium",
                "prompt":f"{prompt.strip()}\n\nTexto a procesar:\n{texto.strip()}"
            },
            stream=True
        )
        if response.status_code == 200:
            csv_respuesta = ""
            for line in response.iter_lines():
                if line:
                    try:
                        line_json = json.loads(line.decode("utf-8"))
                        csv_respuesta += line_json.get("response", "")
                    except json.JSONDecodeError as e:
                        print(f"❌ Error al decodificar JSON: {e}")
                        continue
            if not csv_respuesta.strip():
                print(f"⚠️ La respuesta de Ollama está vacía o no contiene datos procesables.")
                return ""
            print(f"🔍 Respuesta completa de Ollama:\n{csv_respuesta}")
            return limpiar_csv(csv_respuesta).strip()
        else:
            print(f"❌ Error al procesar el texto con Ollama: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"❌ Error al conectarse con Ollama: {e}")
        return ""