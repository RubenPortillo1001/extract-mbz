# Skill: Extraer contenido de cursos Moodle (.mbz) con extract-mbz

## Propósito

Extraer todos los materiales de un backup de curso Moodle (`.mbz`) a una carpeta navegable con:
- Un `HTML` con índice por secciones y links funcionales a cada archivo
- Un `Markdown` listo para subir a Claude y analizar/resumir el contenido del curso
- Una carpeta `materiales/` con todos los archivos (PDFs, DOCXs, páginas HTML, etc.)

---

## Repositorio del script

**GitHub:** `https://github.com/RubenPortillo1001/extract-mbz`  
**Archivo principal:** `extract-mbz.py` (rama `master`)

---

## Requisitos

### En Windows
1. **Python 3** instalado: https://www.python.org/downloads/
2. **Dependencia:** solo `python-slugify`
   ```powershell
   pip install python-slugify
   ```
   > No se necesita `python-magic` ni ninguna otra librería externa. La detección del tipo de archivo (ZIP vs GZIP) se hace leyendo los bytes mágicos del archivo.

### En Linux/Mac
```bash
pip3 install python-slugify
```

---

## Uso

```powershell
python "C:\ruta\al\extract-mbz.py" "C:\ruta\al\backup.mbz"
```

**Ejemplo real:**
```powershell
python "C:\Users\RubenPortillo1\OneDrive\Documents\MDG 2026\extract-mbz-master\extract-mbz.py" "C:\Users\RubenPortillo1\OneDrive\Documents\MDG 2026\copia_de_seguridad-moodle2-course-213-da_2024-20260521-0856-nu.mbz"
```

---

## Estructura de salida

```
<nombre-del-mbz>/           ← carpeta creada junto al .mbz
└── <shortname-del-curso>/  ← nombre corto del curso en Moodle
    ├── <shortname>.html    ← índice navegable con links
    ├── <shortname>.md      ← contenido completo en Markdown (para Claude)
    ├── extract_log.txt     ← log del proceso
    └── materiales/         ← TODOS los archivos del curso
        ├── lectura-base-comprendiendo-llm.html   ← páginas Moodle
        ├── presentacion-semana-1.pdf
        ├── guia-metodologica.docx
        └── ...
```

> **Nota:** Si ya existe una carpeta con el mismo nombre, se crea `<nombre>_1`, `<nombre>_2`, etc. Borrar o renombrar la carpeta anterior antes de re-ejecutar para obtener resultados limpios.

---

## Tipos de módulos Moodle extraídos

| Módulo Moodle | Qué hace el script | Cómo aparece en el HTML/MD |
|---|---|---|
| `resource` | Copia el archivo a `materiales/` | `[Archivo]` con link al archivo |
| `page` | Genera un `.html` con el contenido en `materiales/` | `[Página]` con link al html |
| `url` | Captura el link externo | `[Enlace]` con la URL |
| `folder` | Copia todos los archivos de la carpeta a `materiales/` | `[Carpeta]` con lista de archivos |
| otros (`assign`, `quiz`, `forum`...) | Solo muestra el título con el tipo entre paréntesis | `Título (tipo)` sin link |

---

## Características técnicas del script

### Detección de tipo de archivo .mbz
Los archivos `.mbz` pueden ser ZIP o GZIP. Se detecta por bytes mágicos:
- `PK` (bytes 0-1) → ZIP → se extrae con `zipfile`
- `\x1f\x8b` (bytes 0-1) → GZIP/TAR → se extrae con `tarfile`

### Nombres de archivo seguros para Windows
- Se aplica `slugify()` al nombre original (elimina tildes, caracteres especiales, espacios)
- **Límite de 60 caracteres** en el basename para evitar el límite MAX_PATH de Windows (260 chars total)
- Si hay conflicto de nombres, se añade `(2)`, `(3)`, etc.
- El link HTML siempre apunta al nombre real del archivo guardado

### Extracción de texto para Markdown
La función `strip_html()` convierte el contenido HTML de páginas Moodle a texto plano:
- Convierte `<br>`, `<p>`, `<li>`, `<h1>`–`<h6>` a equivalentes Markdown
- Elimina todas las demás etiquetas HTML
- Decodifica entidades HTML (`&amp;`, `&nbsp;`, etc.)

### Campos opcionales del XML
Versiones modernas de Moodle pueden no incluir algunos campos en `course.xml`.
El script maneja esto con la función `xml_text(root, tag, default='')` que devuelve
un valor por defecto en lugar de crashear si el elemento no existe.
Campos opcionales: `numsections`, `idnumber`, `format`.

---

## Errores comunes y soluciones

### `AttributeError: 'NoneType' object has no attribute 'text'`
**Causa:** Un campo XML no existe en versiones nuevas de Moodle (ej: `numsections`).  
**Solución:** Ya corregido en el script con `xml_text()`. Descargar la versión actual.

### Links del HTML dan error / página no encontrada
**Causa más común:** Ruta total > 260 caracteres en Windows (nombre largo + ruta base larga).  
**Solución:** El script ya limita basenames a 60 chars. Si persiste, mover el archivo `.mbz` a una ruta más corta (ej: `C:\mbz\backup.mbz`).

### El archivo se guarda con nombre diferente al link (ej: `archivo(2).pdf`)
**Causa:** Conflicto de nombres — `add_unique_postfix` cambia el nombre pero el link apuntaba al original.  
**Solución:** Ya corregido — el script extrae el `os.path.basename(destination)` real para construir el link.

### `WARNING: could not copy <archivo>`
**Causa:** El hash del archivo en `files.xml` no coincide con ningún archivo en la carpeta `files/`.  
**Consecuencia:** El link aparece en el HTML pero el archivo no se copiará. Revisar el log.

### Script termina sin generar nada / crash en `open()`
**Causa probable:** La ruta al `.mbz` tiene espacios y no va entre comillas en PowerShell.  
**Solución:** Siempre usar comillas dobles alrededor de las rutas.

---

## Cómo usar el `.md` generado con Claude

1. Ejecutar el script → obtener `<shortname>.md` en la carpeta del curso
2. En claude.ai → nueva conversación → arrastrar el archivo `.md` o usar "Attach file"
3. Ejemplos de prompts útiles:
   - *"Resume el contenido de este curso por secciones"*
   - *"¿Qué temas cubre este curso de doctorado?"*
   - *"Lista todos los recursos y lecturas del curso"*
   - *"Identifica los módulos de evaluación y sus criterios"*
   - *"Genera un syllabus basado en este contenido"*

---

## Instrucciones para Claude al usar este skill

Cuando el usuario quiera extraer materiales de un curso Moodle:

1. **Verificar prerequisitos:** Python 3 instalado, `pip install python-slugify`
2. **Descargar script** desde `https://github.com/RubenPortillo1001/extract-mbz/raw/master/extract-mbz.py`
3. **Construir el comando:**
   ```
   python "<ruta-al-script>\extract-mbz.py" "<ruta-al-archivo.mbz>"
   ```
4. **Verificar salida:** buscar la carpeta `<shortname-del-curso>/` junto al `.mbz`
5. **Si hay error de ruta larga:** mover el `.mbz` a una ruta más corta
6. **Si se quiere re-extraer:** borrar primero la carpeta generada anteriormente

### Señales de que el script funcionó correctamente
- Aparece carpeta `<shortname>/` con subcarpeta `materiales/`
- Existe el archivo `<shortname>.html` con links clickeables
- Existe el archivo `<shortname>.md` con el contenido en texto
- El log `extract_log.txt` muestra secciones y archivos extraídos

### Señales de problema
- Solo existe la carpeta descomprimida pero no la subcarpeta `<shortname>/`
- Los links del HTML dan "archivo no encontrado"
- La carpeta `materiales/` está vacía

---

## Historial de cambios al script original

| Cambio | Motivo |
|---|---|
| Port de Python 2.7 a Python 3 | Python 2 llegó a fin de vida en 2020 |
| Eliminar dependencia `python-magic` | Difícil de instalar en Windows; reemplazado por lectura de bytes mágicos |
| Función `xml_text()` para campos opcionales | Moodle moderno no siempre incluye `numsections` etc. |
| Límite de 60 chars en nombres de archivo | Evita error de MAX_PATH en Windows (260 chars) |
| Usar `os.path.basename(destination)` en links | Corrige links rotos cuando `add_unique_postfix` cambia el nombre |
| Manejo de `page_content = None` | Evita crash en páginas Moodle sin contenido |
| `try/except` en copia de archivos | Warning en lugar de crash al fallar una copia |
| Directorio único `materiales/` en vez de `section_XXX/` | Links siempre funcionales, sin importar la sección |
| Generación de archivo `.md` | Para procesar el contenido del curso con Claude u otros LLMs |
