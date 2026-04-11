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

## Plan activo

**Objetivo:** Migración Total de la Suite a PySide6 e Integración de Intersección 3D.
**Fecha:** 2026-04-11
**Modelo que planificó:** Gemini 3 Flash
**Estado:** 🟠 BLUEPRINT (Esperando EJECUTA)

### Pasos propuestos (MIGRACIÓN)

0. **Verificación de Entorno**
   - Verificar la instalación conjunta de `PySide6` y `rasterio` en `conda`.
   - Actualizar el archivo `README.md` con las nuevas instrucciones de instalación.

1. **Reconstrucción del Core GUI (PySide6) y Dependencias**
   - Actualizar `pyproject.toml` (asegurando compatibilidad de `lxml` y `scipy`).
   - Reimplementar `theme.py` (Tema Claro: `#f9f9f9`, `#ffffff`, `#0078d4`).
   - Reimplementar `widgets.py` (Custom QWidgets: ModernButton, Card, DropZone).
   - Añadir valores default a `config.py` para la herramienta de intersección.

2. **Integración de Intersección (Prioridad 1 en BUILD)**
   - Migrar lógica a `src/landxml_tools/processing/intersection.py`, unificando el parser para usar `io/landxml.py`.
   - Crear la GUI en `src/landxml_tools/gui/interseccion_gui.py` usando Signals (sin usar redirección global de `sys.stdout`).

3. **Migración de Pestañas Existentes (Desacoplamiento)**
   - Eliminar el monolito `apps.py`.
   - Portar Visualizador a `src/landxml_tools/gui/visualizador_gui.py`.
   - Portar Comparador a `src/landxml_tools/gui/comparador_gui.py`.

4. **Orquestación de la Suite y Lanzadores**
   - Nuevo `landxml_suite.py` basado en `QMainWindow` y `QTabWidget` para unir las 3 apps.
   - Actualizar `LandXML Tools.bat` para el nuevo entry point.

5. **Limpieza**
   - Eliminar código huérfano de Tkinter.

## Instrucciones para OpenCode
- **IMPORTANTE**: No mezclar Tkinter con PySide6. La nueva arquitectura debe ser 100% Qt.
- Usa el `implementation_plan.md` del cerebro para detalles técnicos de cada widget.
- Asegura que `ezdxf` esté en las dependencias.
