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

#### [NEW] Función `calculate_hillshade()`

Ubicación: Después de la función `rasterize_surface_tin()` (~línea 376)

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
    # Convertir ángulos a radianes
    azimuth_rad = np.radians(360 - azimuth + 90)  # Ajuste para convención cartográfica
    altitude_rad = np.radians(altitude)
    
    # Calcular gradientes (pendientes) en X e Y
    # Usar np.gradient que maneja bordes correctamente
    dy, dx = np.gradient(grid_z, resolution)
    
    # Calcular pendiente y aspecto
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dx, dy)
    
    # Calcular hillshade usando la fórmula estándar
    hillshade = (
        np.cos(altitude_rad) * np.cos(slope) +
        np.sin(altitude_rad) * np.sin(slope) * np.cos(azimuth_rad - aspect)
    )
    
    # Normalizar a rango 0-1 y manejar NaN
    hillshade = np.clip(hillshade, 0, 1)
    hillshade[np.isnan(grid_z)] = np.nan
    
    return hillshade
```

---

### 2. Modificar `create_surface_map()`

#### [MODIFY] [create_surface_map](file:///e:/GitHub/landxml2image/src/landxml2image.py#L382-L525)

**Nuevos parámetros:**
```python
def create_surface_map(grid_z, extent, output_name, colormap='terrain',
                       save_png_alpha=True, save_jpg=True, output_dir=None,
                       class_interval=None, whitening=0.0,
                       hillshade=False, hillshade_intensity=0.5,  # NUEVO
                       hillshade_azimuth=315, hillshade_altitude=45):  # NUEVO
```

**Nueva lógica después de aplicar whitening (~línea 453):**
```python
# Aplicar hillshade (después del whitening)
if hillshade:
    # Calcular resolución desde extent
    xmin, xmax, ymin, ymax = extent
    resolution = (xmax - xmin) / grid.shape[1]
    
    # Calcular sombreado
    hs = calculate_hillshade(grid, hillshade_azimuth, hillshade_altitude, resolution)
    
    # Transponer para coincidir con orientación del grid
    hs = hs.T
    
    # Blend: colormap * (1 - intensity) + colormap * hillshade * intensity
    # Esto oscurece las zonas en sombra manteniendo los colores
    hillshade_intensity = max(0.0, min(1.0, hillshade_intensity))
    print(f"  Aplicando hillshade: azimut={hillshade_azimuth}°, altitud={hillshade_altitude}°, intensidad={hillshade_intensity*100:.0f}%")
    
    # Expandir hillshade a 3 canales para multiplicar con RGB
    hs_rgb = np.stack([hs, hs, hs], axis=2)
    
    # Aplicar blend
    rgb = rgb * (1 - hillshade_intensity) + rgb * hs_rgb * hillshade_intensity
    rgb = np.clip(rgb, 0, 1)
```

---

### 3. Modificar `create_colormap_legend()`

#### [MODIFY] [create_colormap_legend](file:///e:/GitHub/landxml2image/src/landxml2image.py#L584-L676)

**Nuevos parámetros:**
```python
def create_colormap_legend(grid_z, colormap='terrain', output_name='superficie',
                           png=True, jpg=True, font_name='Inter', font_size=12, 
                           output_dir=None, class_interval=None, whitening=0.0,
                           hillshade=False):  # NUEVO (solo para indicador)
```

**Opcional:** Añadir nota en la leyenda si hillshade está activo.

---

### 4. Modificar `process_landxml()`

#### [MODIFY] [process_landxml](file:///e:/GitHub/landxml2image/src/landxml2image.py#L682-L775)

**Nuevos parámetros:**
```python
def process_landxml(surface_file, output_name, resolution, epsg_code, colormap,
                    save_jpg, save_png, save_tiff, save_legend, output_dir=None,
                    class_interval=None, whitening=0.0, progress_callback=None,
                    hillshade=False, hillshade_intensity=0.5,  # NUEVO
                    hillshade_azimuth=315, hillshade_altitude=45):  # NUEVO
```

**Pasar parámetros a las funciones llamadas.**

---

### 5. Modificar GUI (`LandXMLImageGUI`)

#### [MODIFY] [LandXMLImageGUI.__init__](file:///e:/GitHub/landxml2image/src/landxml2image.py#L864-L900)

**Nuevas variables:**
```python
# Variables para hillshade
self.hillshade_var = tk.BooleanVar(value=False)
self.hillshade_intensity_var = tk.IntVar(value=50)  # 0-100%
```

#### [MODIFY] Sección de efectos en `create_widgets()`

Añadir después de los controles de whitening:

```python
# --- Hillshade ---
hillshade_frame = tk.Frame(effects_frame, bg=COLORS['light'])
hillshade_frame.pack(fill=tk.X, pady=(SPACING['SMALL'], 0))

self.hillshade_check = tk.Checkbutton(
    hillshade_frame,
    text="Hillshade (sombreado)",
    variable=self.hillshade_var,
    font=FONTS['body'],
    bg=COLORS['light'],
    fg=COLORS['text'],
    command=self.on_hillshade_toggle
)
self.hillshade_check.pack(side=tk.LEFT)
ToolTip(self.hillshade_check, "Aplica efecto de iluminación solar para resaltar el relieve")

# Slider de intensidad (inicialmente oculto o deshabilitado)
self.hillshade_intensity_frame = tk.Frame(hillshade_frame, bg=COLORS['light'])
self.hillshade_intensity_frame.pack(side=tk.LEFT, padx=(SPACING['MEDIUM'], 0))

tk.Label(
    self.hillshade_intensity_frame,
    text="Intensidad:",
    font=FONTS['small'],
    bg=COLORS['light'],
    fg=COLORS['text']
).pack(side=tk.LEFT)

self.hillshade_slider = tk.Scale(
    self.hillshade_intensity_frame,
    from_=0, to=100,
    orient=tk.HORIZONTAL,
    variable=self.hillshade_intensity_var,
    length=100,
    showvalue=False,
    bg=COLORS['light'],
    highlightthickness=0
)
self.hillshade_slider.pack(side=tk.LEFT)

self.hillshade_intensity_label = tk.Label(
    self.hillshade_intensity_frame,
    text="50%",
    font=FONTS['small'],
    bg=COLORS['light'],
    fg=COLORS['text'],
    width=4
)
self.hillshade_intensity_label.pack(side=tk.LEFT)
```

#### [MODIFY] Método `run_process()`

Añadir lectura de las nuevas variables y pasarlas a `process_landxml()`.

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
- [ ] Preview en la GUI actualiza con hillshade (si aplica)

---

## Resumen de archivos afectados

| Archivo                | Cambios                                                        |
| ---------------------- | -------------------------------------------------------------- |
| `src/landxml2image.py` | Nueva función + modificaciones en 4 funciones existentes + GUI |

**Complejidad estimada:** Media-baja (~2-3 horas)

**Dependencias nuevas:** Ninguna (usa NumPy existente)
