# CHANGELOG.md - Historial de cambios de LandXML Tools

## 2026-04-11

### Iteración 4.0 — Refactorización Profunda y Limpieza del Proyecto (Hito Final)

- **Archivos:** theme.py, widgets.py, *_gui.py, apps/, README.md
- **Cambio:** refactorización total + eliminación de código legacy
- **Ejecutado por:** Antigravity (Advanced Agentic Coding)
- **Nota:**
  - **Arquitectura de Estilos**: Eliminación de 500+ líneas de CSS inline. Migración a selectores de clase y propiedades dinámicas en `theme.py`.
  - **Optimización Vertical**: Reajuste de espaciado y alturas de componentes para eliminar el scroll en todas las pestañas.
  - **Flexibilidad de Layout**: El Log de consola ahora es el componente elástico principal.
  - **Limpieza de Proyecto**: Eliminación definitiva de los restos de **Tkinter** (`gui/apps.py`, `apps/landxml2image.py`).
  - **Documentación**: Actualización total de `README.md` y `AGENTS.md` para reflejar la nueva suite profesional en PySide6.

---


### Iteración 3.1 — Refinamiento UX/UI Finalizado

- **Archivos:** theme.py, widgets.py, visualizador_gui.py, comparador_gui.py, interseccion_gui.py
- **Cambio:** editar (múltiples archivos)
- **Ejecutado por:** minimax-m2.5-free (OpenCode)
- **Revisado por:** minimax-m2.5-free (OpenCode)
- **Nota:**
  - Compactación vertical extrema ( Cards 90px, iconos reducidos)
  - Visibilidad inputs reforzados (2px solid #888)
  - Botones Examinar con #BrowseButton
  - Consolidación Salida con getSaveFileName

---

## 2026-04-11

### Iteración 3 — Refinamiento UX/UI Definitivo

- **Archivos:** theme.py, widgets.py, visualizador_gui.py, comparador_gui.py, interseccion_gui.py
- **Cambio:** editar (múltiples archivos)
- **Ejecutado por:** minimax-m2.5-free (OpenCode)
- **Revisado por:** minimax-m2.5-free (OpenCode)
- **Nota:** 
  - Card margins compactados (SPACING['lg'] → SPACING['md'])
  - Visualizador: fusión de campos "Nombre" + "Directorio" → "Salida:" con getSaveFileName
  - Comparador: fusión de campos "Nombre" + "Directorio" → "Salida:" con getSaveFileName
  - Intersección: eliminación de checkbox EPSG, solo SpinBox editable con autodetección

---

## 2026-04-11

### Iteración 2 — Refinamiento UI/UX PySide6

- **Archivos:** theme.py, visualizador_gui.py, comparador_gui.py, interseccion_gui.py
- **Cambio:** editar (múltiples archivos)
- **Ejecutado por:** minimax-m2.5-free (OpenCode)
- **Revisado por:** minimax-m2.5-free (OpenCode)
- **Nota:** 
  - PrimaryButton disabled ahora visible (#a0a0a0)
  - QListWidget para gestionar archivos en Visualizador y Comparador
  - QTextEdit#ConsoleLog con estilo dark
  - EPSG con autodetección desde coordenadas
  - Botones "Examinar" con clase .BrowseButton