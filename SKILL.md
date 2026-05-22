---
name: extract-mbz
description: >
  Extrae y visualiza materiales de un curso Moodle desde un archivo backup .mbz.
  Ejecuta el script Python directamente en la PC del usuario via Desktop Commander.
  El runtime ya está desplegado en C:\ClaudeSkills\extract-mbz\.
  USAR SIEMPRE que el usuario mencione: backup de Moodle, archivo .mbz,
  extraer curso Moodle, visualizar curso Moodle, "procesá el backup de Moodle",
  o indique una ruta a un archivo .mbz.
---

# Skill: Extractor de Cursos Moodle (.mbz)

## Arquitectura

- **Runtime en PC:** `C:\ClaudeSkills\extract-mbz\`
  - `extract-mbz.py` — script principal
  - `tachyons.css` — estilos del reporte HTML
- **Script fuente original:** `C:\Users\RubenPortillo1\OneDrive\Documents\MDG 2026\extract-mbz-master\`

## Paso 0 — Verificar runtime

Antes de ejecutar, verificar que los archivos existen:

```powershell
Test-Path "C:\ClaudeSkills\extract-mbz\extract-mbz.py"
Test-Path "C:\ClaudeSkills\extract-mbz\tachyons.css"
```

Si alguno falta, copiar desde el directorio fuente:

```powershell
Copy-Item "C:\Users\RubenPortillo1\OneDrive\Documents\MDG 2026\extract-mbz-master\extract-mbz.py" "C:\ClaudeSkills\extract-mbz\"
Copy-Item "C:\Users\RubenPortillo1\OneDrive\Documents\MDG 2026\extract-mbz-master\tachyons.css" "C:\ClaudeSkills\extract-mbz\"
```

## Paso 1 — Obtener la ruta del archivo .mbz

Pedirle al usuario la ruta completa del archivo `.mbz`. Ejemplo:
`C:\Users\RubenPortillo1\Downloads\backup-moodle2-course-123.mbz`

## Paso 2 — Ejecutar la extracción

```powershell
cd "C:\ClaudeSkills\extract-mbz"
python extract-mbz.py "RUTA_DEL_ARCHIVO.mbz"
```

Reemplazar `RUTA_DEL_ARCHIVO.mbz` con la ruta real proporcionada por el usuario.

## Paso 3 — Reportar resultados

El script genera tres salidas en el mismo directorio del `.mbz`:

| Archivo | Uso |
|---|---|
| `[nombre].html` | Abrir en navegador para navegar el curso |
| `[nombre].md` | Analizar contenido con el agente |
| `extract_log.txt` | Auditar el proceso de extracción |

Informar al usuario las rutas exactas de los tres archivos generados.

## Paso 4 — Re-desplegar runtime (si fue borrado)

Si el runtime no existe, copiarlo desde el directorio fuente (ver Paso 0).
Si el directorio fuente tampoco existe, solicitar al usuario el script original.

## Notas técnicas

- El script detecta ZIP vs GZIP por bytes mágicos — no requiere librerías externas para eso
- `tachyons.css` debe estar en el mismo directorio que `extract-mbz.py` en tiempo de ejecución
- Compatible con Python 3.x sin dependencias adicionales
