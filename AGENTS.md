# AGENTS.md - Guía de Desarrollo para LandXML Tools

Este documento centraliza los estándares y hitos del proyecto para agentes de IA (Antigravity, OpenCode).

## Arquitectura Actual (PySide6)

El proyecto ha sido migrado íntegramente a **PySide6** y utiliza un sistema de temas centralizado para evitar la dispersión de estilos.

### Estándares de Estilo (QSS)
- **NUNCA** utilices `setStyleSheet` directamente en los widgets de las pestañas (`*_gui.py`).
- Los estilos deben definirse en `src/landxml_tools/gui/theme.py` utilizando selectores de clase.
- Para aplicar un estilo a un contenedor, usa: `widget.setProperty("class", "ClaseDeseada")`.
- Clases disponibles actualmente:
    - `Card`: Para contenedores con borde y título.
    - `HRow`: Para filas horizontales de parámetros.
    - `FileDropBox`: Para zonas de selección de archivos.
    - `#PrimaryButton`: ID para el botón principal de acción.
    - `#BrowseButton`: ID para botones de "Examinar".
    - `#ConsoleLog`: ID para la consola de salida dark.

### Guía de Interfaz
- **Labels**: Deben ser siempre transparentes y sin bordes (por defecto en el tema global).
- **Inputs**: Solo los campos editables (`QLineEdit`, `QSpinBox`) deben tener bordes visibles para indicar interactividad.
- **Flexibilidad**: El componente de Log debe configurarse con `setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)` para absorber el espacio sobrante de la ventana.

## Hitos Alcanzados (2026-04)

- ✅ **Suite Unificada**: Integración de Visualizador, Comparador e Intersección 3D.
- ✅ **Intersección 3D**: Implementación robusta del algoritmo Guigue-Devillers.
- ✅ **Refactorización Core**: Transición total de Tkinter a PySide6.
- ✅ **Optimización de UI**: Interfaz compacta sin scroll y altamente reactiva.
- ✅ **Limpieza de Proyecto**: Eliminación de código heredado y redundante.

---

## Instrucciones para Agentes de Mantenimiento

1.  Conserva siempre la estructura de `Card` -> `content_layout()` para añadir parámetros.
2.  Usa los helpers de `SPACING` definidos en `theme.py` para márgenes y paddings.
3.  Cualquier nueva herramienta debe añadirse como una pestaña en `landxml_suite.py` siguiendo el patrón de `LandXMLIntersectionGUI`.
4.  Mantén el `README.md` sincronizado con las capacidades reales de la Suite.
