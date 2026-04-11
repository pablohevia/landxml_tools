# CHANGELOG.md - Historial de cambios de LandXML Tools

## 2026-04-11

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