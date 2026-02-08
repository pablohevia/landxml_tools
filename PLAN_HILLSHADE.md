# Plan de Implementación: Efecto Hillshade

## Descripción

El efecto **Hillshade** (sombreado de relieve) simula la iluminación solar sobre el terreno, creando una representación visual que resalta las formas del relieve. Se combina con el mapa de colores existente para producir una visualización más realista y legible del terreno.

### Parámetros del efecto

| Parámetro      | Valor típico | Descripción                                           |
| -------------- | ------------ | ----------------------------------------------------- |
| **Azimut**     | 315°         | Dirección del sol (0°=Norte, 90°=Este, 315°=Noroeste) |
| **Altitud**    | 45°          | Elevación del sol sobre el horizonte                  |
| **Intensidad** | 50%          | Cuánto del efecto se aplica sobre el colormap         |

---

## Cambios Propuestos

### 1. Nueva función de cálculo Hillshade

#### [NEW] `calculate_hillshade()` en [raster.py](file:///e:/GitHub/landxml_tools/src/landxml_tools/processing/raster.py)

```python
def calculate_hillshade(grid_z, azimuth=315, altitude=45, resolution=1.0):
    """
    Calcula el sombreado de relieve (hillshade) a partir de un grid de elevaciones.
    
    Args:
        grid_z (numpy.ndarray): Grid 2D con elevaciones (puede contener NaN)
        azimuth (float): Ángulo del sol en grados (0=Norte, 90=Este, 315=Noroeste)
        altitude (float): Elevación del sol sobre el horizonte en grados (0-90)
        resolution (float): Tamaño de celda en metros (para escalar gradientes)
    
    Returns:
        numpy.ndarray: Grid 2D con valores de sombreado normalizados (0-1)
    """
    azimuth_rad = np.radians(360 - azimuth + 90)
    altitude_rad = np.radians(altitude)
    dy, dx = np.gradient(grid_z, resolution)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dx, dy)
    hillshade = (
        np.cos(altitude_rad) * np.cos(slope) +
        np.sin(altitude_rad) * np.sin(slope) * np.cos(azimuth_rad - aspect)
    )
    hillshade = np.clip(hillshade, 0, 1)
    hillshade[np.isnan(grid_z)] = np.nan
    return hillshade
```

---

### 2. Modificar `save_colored_map()`

#### [MODIFY] [plotting.py](file:///e:/GitHub/landxml_tools/src/landxml_tools/viz/plotting.py)

**Nuevos parámetros:**
```python
def save_colored_map(grid_z, output_name, colormap='terrain', output_dir=None,
                     class_interval=None, whitening=0.0, center_zero=False,
                     save_png=True, save_jpg=True, rotate_90=False,
                     hillshade=False, hillshade_intensity=0.5,  # NUEVO
                     hillshade_azimuth=315, hillshade_altitude=45):  # NUEVO
```

**Nueva lógica después de aplicar whitening:**
```python
if hillshade:
    from landxml_tools.processing.raster import calculate_hillshade
    resolution = 1.0  # O calcular desde extent si está disponible
    hs = calculate_hillshade(grid, hillshade_azimuth, hillshade_altitude, resolution)
    hs_rgb = np.stack([hs, hs, hs], axis=2)
    rgb = rgb * (1 - hillshade_intensity) + rgb * hs_rgb * hillshade_intensity
    rgb = np.clip(rgb, 0, 1)
```

---

### 3. Modificar GUI (`LandXMLImageGUI`)

#### [MODIFY] [apps.py](file:///e:/GitHub/landxml_tools/src/landxml_tools/gui/apps.py)

**Nuevas variables en `__init__`:**
```python
self.hillshade_var = tk.BooleanVar(value=False)
self.hillshade_intensity_var = tk.IntVar(value=50)
```

**Nuevos controles en `_create_ui` (después de whitening):**
```python
# Hillshade
hillshade_row = tk.Frame(config_card.content, bg=COLORS['bg_white'])
hillshade_row.pack(fill=tk.X, pady=(SPACING['xs'], 0))

StyledCheckbox(hillshade_row, "Hillshade", self.hillshade_var).pack(side=tk.LEFT)

tk.Label(hillshade_row, text="Intensidad:", font=FONTS['body'],
        bg=COLORS['bg_white'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(SPACING['lg'], SPACING['xs']))

self.hillshade_scale = tk.Scale(hillshade_row, from_=0, to=100, orient=tk.HORIZONTAL,
                                variable=self.hillshade_intensity_var, length=120,
                                bg=COLORS['bg_white'], highlightthickness=0, showvalue=0)
self.hillshade_scale.pack(side=tk.LEFT)

self.hillshade_spin = tk.Spinbox(hillshade_row, from_=0, to=100,
                                textvariable=self.hillshade_intensity_var, width=4, font=FONTS['body'])
self.hillshade_spin.pack(side=tk.LEFT, padx=(SPACING['xs'], 0))
tk.Label(hillshade_row, text="%", font=FONTS['body'], bg=COLORS['bg_white']).pack(side=tk.LEFT)
```

**Modificar `_run_processing` para pasar los nuevos parámetros a `save_colored_map()`.**

---

### 4. Aplicar también a `LandXMLDiffGUI`

Los mismos cambios de GUI se replican en la clase `LandXMLDiffGUI` dentro de [apps.py](file:///e:/GitHub/landxml_tools/src/landxml_tools/gui/apps.py).

---

## Verificación

### Tests manuales

1. **Sin Hillshade**: Verificar que el comportamiento actual no cambia
2. **Con Hillshade al 50%**: Verificar que se aplica sombreado visible
3. **Hillshade + Whitening**: Verificar que ambos efectos se combinan correctamente
4. **Hillshade + Clasificación**: Verificar que funciona con intervalos discretos

### Archivos a verificar

- [ ] PNG con transparencia muestra hillshade correctamente
- [ ] JPG muestra hillshade correctamente

---

## Resumen de archivos afectados

| Archivo                                  | Cambios                                     |
| ---------------------------------------- | ------------------------------------------- |
| `src/landxml_tools/processing/raster.py` | Nueva función `calculate_hillshade()`       |
| `src/landxml_tools/viz/plotting.py`      | Modificar `save_colored_map()`              |
| `src/landxml_tools/gui/apps.py`          | Modificar ambas clases GUI                  |
| `apps/landxml_diff.py`                   | Pasar nuevos parámetros en función `main()` |

**Complejidad estimada:** Media-baja (~2-3 horas)

**Dependencias nuevas:** Ninguna (usa NumPy existente)
