# Lector de Facturas PDF con OCR y Ollama

Este proyecto permite extraer, estructurar y almacenar datos de facturas en PDF utilizando Python, OCR (Tesseract) y modelos LLM (Ollama). Los datos extraídos se guardan en una base de datos SQLite para su posterior análisis o gestión.

## Características

- Extracción de texto desde PDFs, incluso si contienen imágenes (OCR).
- Estructuración automática de los datos de la factura usando un modelo LLM (Ollama).
- Almacenamiento de los datos estructurados en una base de datos SQLite.
- Soporte para múltiples facturas y carpetas.
- Código modular y fácil de mantener.

## Requisitos

- Python 3.8 o superior
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado y en el PATH
- [Ollama](https://ollama.com/) corriendo localmente con el modelo `phi3:medium`
- Dependencias Python (ver `requirements.txt`)

## Instalación

1. **Clona el repositorio:**
   ```sh
   git clone https://github.com/Matihus00/LectordeFacturas.git
   cd LectordeFacturas
   ```

2. **Instala las dependencias de Python:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Instala Tesseract OCR:**
   - Descárgalo desde [aquí](https://github.com/tesseract-ocr/tesseract).
   - Asegúrate de que la ruta esté correctamente configurada en `funciones.py`:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     ```

## Configuración de variable de entorno

- Por defecto, el script busca las facturas en la carpeta `facturas/` dentro del proyecto.
- Puedes cambiar la ruta usando la variable de entorno `FACTURAS_PATH` antes de ejecutar el script:

  **En Windows (CMD):**
  ```sh
  set FACTURAS_PATH=C:\ruta\a\tus\facturas
  python main.py
  ```

  **En Linux/Mac o PowerShell:**
  ```sh
  export FACTURAS_PATH="/ruta/a/tus/facturas"
  python main.py
  ```

## Ejecución del modelo Ollama

1. **Instala Ollama** siguiendo su [documentación oficial](https://ollama.com/).
2. **Descarga el modelo adecuado** (por ejemplo, `phi3:medium`):
   ```sh
   ollama pull phi3:medium
   ```
3. **Ejecuta el servidor Ollama**:
   ```sh
   ollama run phi3:medium
   ```
   Asegúrate de que Ollama esté corriendo antes de ejecutar tu script de facturas.

## Uso

1. Coloca tus archivos PDF de facturas en la carpeta indicada (`facturas/` por defecto o la que configures).
2. Ejecuta el script principal:
   ```sh
   python main.py
   ```
3. Los datos extraídos y estructurados se guardarán en `facturas.db`.

## Estructura del proyecto

```
.
├── main.py
├── funciones.py
├── Ollama_utils.py
├── requirements.txt
├── .gitignore
├── README.md
└── facturas/           # (No subir PDFs reales)
```

## Notas

- **No subas archivos de facturas reales ni datos sensibles al repositorio.**
- Si quieres compartir ejemplos, usa archivos ficticios o anonimizados.
- Puedes modificar el prompt de Ollama en `Ollama_utils.py` para adaptarlo a tus necesidades.
- Si tienes problemas con dependencias, revisa que tu entorno virtual esté activado y actualizado.

## Licencia

Este proyecto está licenciado bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
