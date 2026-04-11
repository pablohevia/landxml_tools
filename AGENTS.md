# AGENTS.md - Guidelines for LandXML Tools

## Project Overview
LandXML Tools is a Python library for processing and visualizing LandXML surface data (TIN - Triangulated Irregular Networks). It provides tools for rasterization, hillshade calculation, surface comparison, and GeoTIFF/World File export.

## Dependencies
- numpy, matplotlib, scipy, lxml, pillow, rasterio
- Python 3.9+

## Build & Installation
```bash
# Development install
pip install -e .

# Install with conda (recommended for rasterio on Windows)
conda create -n landxml_env python=3.9 rasterio
conda activate landxml_env
pip install -e .
```

## Running the Application
```bash
# Suite (GUI with all tools)
python landxml_suite.py

# Visualizador standalone (GUI)
python -m apps.landxml2image

# Comparador CLI
python -m apps.landxml_diff --file1 base.xml --file2 comparacion.xml
```

## Testing
**No test suite currently exists.** When adding tests:
```bash
# Run pytest (if tests are added)
pytest test/

# Run single test file
pytest test/test_raster.py

# Run single test function
pytest test/test_raster.py::test_rasterize_surface_tin
```

## Code Style Guidelines

### General
- Project language is **Spanish** (docstrings, comments, user-facing messages)
- Code is generally clean and well-organized
- Follow existing patterns in the codebase

### Imports
```python
# Standard library first
import os
import sys
import json

# Third-party
import numpy as np
import matplotlib.pyplot as plt
from lxml import etree

# Local imports (relative)
from .tin import validate_and_clean_triangulation
from ..io.landxml import parse_landxml_surface
```

### Type Hints
Use type hints in function signatures:
```python
def rasterize_surface_tin(
    points: np.ndarray,
    triangles: np.ndarray | None,
    resolution: float = 0.05,
    extent: list | None = None
) -> tuple[np.ndarray, list]:
```

### Naming Conventions
- **Functions/methods**: `snake_case` (e.g., `parse_landxml_surface`, `calculate_hillshade`)
- **Classes**: `PascalCase` (e.g., `LandXMLImageGUI`, `ModernButton`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `COLORS`, `FONTS`)
- **Private members**: prefix with underscore (e.g., `_create_ui`, `_config`)

### Docstrings
Use NumPy-style docstrings in Spanish:
```python
def parse_landxml_surface(xml_file: str):
    """
    Parsea un archivo LandXML y extrae los puntos y triángulos de la superficie TIN.
    
    Args:
        xml_file (str): Ruta al archivo LandXML a parsear.
    
    Returns:
        tuple: Una tupla (points, triangles) donde:
            - points (ndarray): Array de forma (n, 3) con coordenadas [X, Y, Z]
            - triangles (ndarray | None): Array de forma (m, 3) con índices de vértices.
    
    Raises:
        ValueError: Si no se encuentra el elemento <Surface> o <Pnts>.
    """
```

### Error Handling
- Use `try/except` for operations that may fail (file I/O, parsing)
- Raise `ValueError` for invalid input parameters
- Provide meaningful error messages in Spanish
```python
if surface is None:
    raise ValueError(f"No se encontró <Surface> en {xml_file}")
```

### GUI Development (tkinter)
- Use `ttk` widgets when possible
- Separate UI creation into `_create_ui()` method
- Run long operations in separate threads with `threading.Thread(target=..., daemon=True)`
- Use `root.after(0, callback)` to update UI from background threads
- Follow theme constants from `gui.theme` (COLORS, FONTS, SPACING)

### NumPy Conventions
- Use `np.ndarray` type alias in hints
- Arrays are typically shape `(n, 3)` for points `[X, Y, Z]` or `(rows, cols)` for grids
- Use `np.nan` for NoData values
- Prefer `np.array()` over `np.asarray()` when you need a copy

### File Organization
```
src/landxml_tools/
├── __init__.py          # Package init, version
├── config.py            # Configuration management
├── gui/                 # Tkinter GUI components
│   ├── apps.py          # Main GUI classes
│   ├── widgets.py       # Reusable widgets
│   └── theme.py         # Theme constants
├── io/                  # Input/Output
│   ├── landxml.py       # LandXML parsing
│   └── export.py        # GeoTIFF/World File export
├── processing/          # Core algorithms
│   ├── raster.py        # TIN rasterization
│   ├── tin.py           # TIN validation
│   ├── diff.py          # Surface comparison
│   └── hillshade.py     # Hillshade calculation
└── viz/                  # Visualization
    └── plotting.py      # Matplotlib plotting

apps/                    # Application entry points
test/                    # Test files (add when needed)
```

### Configuration
- Default config lives in `config.json` in project root
- Use `config.py` functions: `get(section, key)`, `get_section(section)`
- Fallback defaults in `config.py` if JSON file missing

## Editor Settings
VS Code settings (`.vscode/settings.json`):
```json
{
    "python-envs.defaultEnvManager": "ms-python.python:conda",
    "python-envs.defaultPackageManager": "ms-python.python:conda"
}
```

## Key Libraries
- **numpy**: Array operations, gradient calculation
- **matplotlib**: Triangulation, colormaps, plotting
- **scipy**: Delaunay triangulation (via matplotlib)
- **lxml**: XML parsing for LandXML files
- **rasterio**: GeoTIFF read/write
- **PIL/Pillow**: Image manipulation
- **tkinter**: GUI (stdlib)

## Hilo de colaboración

<!-- AGENT_RELAY
from: Gemini (3 Flash)
to: Gemini (3.1 Pro High)
topic: Requesting refinement of UI elements based on screenshots. Buttons look flat, select boxes don't use D&D, EPSG has arrows.
-->

<!-- AGENT_RELAY
from: Gemini (3.1 Pro High)
to: Gemini (Flash / Low / OpenCode)
topic: Plan de refinamiento y unificación UI/UX
turn: 10
phase: BUILD
mode: Synthesis
-->
**Contexto:** Se ha completado la migración de Tkinter a PySide6 de toda la suite. Sin embargo, hay discrepancias en el diseño de los componentes: cajas de archivos que parecen selectores, botones fantasma por contrastes de colores y spinners numéricos que estorban. He diseñado un plan en `implementation_plan.md` que propone la creación de un componente `FileDropBox` universal para que todas las pestañas se usen y se sientan idénticas.

**Para ti:** Te he dejado la solución arquitectónica estructurada. Cuando se pulse "Ejecutar", tu objetivo es leer el `implementation_plan.md` y aplicarlo sobre el código ya existente de PySide6 para uniformar la UX.

---

## Protocolo de Colaboración (Ciclo de Vida)

### Estados de un paso
- `pendiente` — planificado, sin ejecutar
- `para revisión` — ejecutado, esperando validación del revisor
- `completado` — validado Y verificado funcionalmente por el revisor
- `fallido` — validación negativa; requiere corrección

### Flujo de validación (REVISOR)

El **agente revisor** es el **único responsable** de estos pasos finales:

#### 1. Verificar código
- Revisa que el código cumple los requisitos del paso
- Compara con lo planificado en AGENTS.md

#### 2. Verificar funcionalmente
- **OBLIGATORIO**: Ejecutar la aplicación para probar los cambios
- Para proyectos GUI: `python landxml_suite.py` y verificar visualmente
- Para CLI: probar los comandos relevantes
- Si es un fix: verificar que el problema original está resuelto

#### 3. Archivar (solo si ambas verificaciones pasan)
- Añadir el paso a `CHANGELOG.md`
- Eliminar el paso de `AGENTS.md`
- Estas dos acciones son **inseparables**: no se puede archivar sin borrar, ni borrar sin archivar

### Si la verificación falla
- Cambiar estado a `fallido`
- Añadir nota explicando qué falló
- Proponer plan de corrección en 2-3 líneas
- Devolver a `pendiente` para que el coder lo corregja

### Definición de "verificación funcional"
- Ejecutar la aplicación
- Probar las funcionalidades modificadas
- Verificar que los cambios funcionan como se esperaba
- **No es solo revisar el código**
