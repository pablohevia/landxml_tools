"""
Módulo de visualización y generación de gráficos.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image

def create_colormap_legend(grid, colormap='terrain', output_path=None,
                           font_name='Inter', font_size=12,
                           class_interval=None, whitening=0.0,
                           center_zero=False):
    """
    Genera una leyenda de colormap como imagen.
    
    Args:
        grid (ndarray): Array 2D con valores.
        colormap (str): Nombre del colormap.
        output_path (str): Ruta completa al archivo de salida (si es None, no guarda).
        font_name (str): Nombre de la fuente.
        font_size (int): Tamaño de fuente.
        class_interval (float | None): Intervalo de clasificación.
        whitening (float): Factor de blanqueamiento (0.0 - 1.0).
        center_zero (bool): Si True, centra la escala en 0 (útil para diferencias).
    """
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    valid_data = grid[~np.isnan(grid)]
    if len(valid_data) == 0:
        return

    # Filtrado de ruido numérico (epsilon = 1mm)
    EPSILON = 1e-3
    valid_data_filtered = np.where(np.abs(valid_data) < EPSILON, 0.0, valid_data)
    
    vmin, vmax = valid_data_filtered.min(), valid_data_filtered.max()
    
    # Configurar normalización
    if center_zero:
        abs_max = max(abs(vmin), abs(vmax))
        vmin, vmax = -abs_max, abs_max
        norm_type = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    else:
        norm_type = plt.Normalize(vmin=vmin, vmax=vmax)

    # Preparar colormap
    base_cmap = plt.get_cmap(colormap)
    if whitening > 0:
        whitening = max(0.0, min(1.0, whitening))
        colors = base_cmap(np.linspace(0, 1, 256))
        colors[:, :3] = colors[:, :3] * (1 - whitening) + whitening
        cmap = mcolors.ListedColormap(colors, name=f"{colormap}_whitened")
    else:
        cmap = base_cmap
    
    # Ajustar para intervalos discretos
    norm = norm_type
    if class_interval is not None and class_interval > 0:
        if center_zero:
            # Discretización simétrica igual que en save_colored_map
            vmin_disc = np.sign(vmin) * np.floor(np.abs(vmin) / class_interval) * class_interval
            vmax_disc = np.sign(vmax) * np.floor(np.abs(vmax) / class_interval) * class_interval
            # Asegurar simetría perfecta
            abs_max_disc = max(abs(vmin_disc), abs(vmax_disc))
            vmin_disc = -abs_max_disc
            vmax_disc = abs_max_disc
            # Limpiar -0.0 -> 0.0
            vmin_disc = 0.0 if abs(vmin_disc) < EPSILON else vmin_disc
            vmax_disc = 0.0 if abs(vmax_disc) < EPSILON else vmax_disc
            boundaries = np.arange(vmin_disc, vmax_disc + class_interval + 0.001, class_interval)
            if len(boundaries) > 1:
                norm = mcolors.BoundaryNorm(boundaries, cmap.N)
        else:
            vmin_disc = np.floor(vmin / class_interval) * class_interval
            vmax_disc = np.ceil(vmax / class_interval) * class_interval
            boundaries = np.arange(vmin_disc, vmax_disc + class_interval + 0.001, class_interval)
            if len(boundaries) > 1:
                norm = mcolors.BoundaryNorm(boundaries, cmap.N)

    # Crear figura
    fig, ax = plt.subplots(figsize=(2, 6))
    ax.axis('off')
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=1.0, pad=0.05)
    cbar.ax.yaxis.set_ticks_position('right')
    cbar.outline.set_visible(False)
    
    label = "Diferencia [m]" if center_zero else "Elevación [m]"
    cbar.set_label(label, fontsize=font_size, fontname=font_name)
    
    for tick in cbar.ax.get_yticklabels():
        try:
            tick.set_fontname(font_name)
            tick.set_fontsize(font_size)
        except Exception:
            pass
    
    if output_path:
        fig.savefig(output_path, bbox_inches='tight', dpi=300, transparent=True)
        print(f"  Leyenda guardada → {output_path}")
    
    plt.close(fig)

def save_colored_map(grid, output_name, colormap='terrain', output_dir=None,
                     class_interval=None, whitening=0.0, center_zero=False,
                     save_png=True, save_jpg=True, rotate_90=True,
                     hillshade=False, hillshade_intensity=0.5,
                     hillshade_azimuth=315, hillshade_altitude=45,
                     resolution=1.0):
    """
    Genera y guarda imágenes coloreadas (PNG/JPG) del grid.
    
    Args:
        grid (ndarray): Array 2D con valores de elevación/diferencia.
        output_name (str): Nombre base para los archivos.
        colormap (str): Nombre del colormap.
        output_dir (str | None): Directorio de salida.
        class_interval (float | None): Intervalo de clasificación.
        whitening (float): Factor de blanqueamiento (0.0 - 1.0).
        center_zero (bool): Si True, centra la escala en 0 (útil para diferencias).
        save_png (bool): Guardar PNG con transparencia.
        save_jpg (bool): Guardar JPG.
        rotate_90 (bool): Rotar 90 grados antihorario (necesario para orientación correcta).
        hillshade (bool): Si True, aplica efecto de sombreado de relieve.
        hillshade_intensity (float): Intensidad del hillshade (0.0 - 1.0).
        hillshade_azimuth (float): Ángulo del sol (0=Norte, 315=Noroeste).
        hillshade_altitude (float): Elevación del sol (0-90 grados).
        resolution (float): Resolución del grid en metros (para cálculo correcto del hillshade).
    """
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_base = os.path.join(output_dir, output_name)
    else:
        out_base = output_name
        
    png_path = f"{out_base}.png"
    jpg_path = f"{out_base}.jpg"
    
    # Transponer si es necesario (la lógica original transponía el grid antes de procesar)
    # Pero aquí recibimos el grid generado por rasterize_surface_tin que es (Y, X)
    # La lógica original de landxml2image hacía:
    # grid = grid_z.T 
    # height, width = grid.shape
    # ...
    # img_pil = img_pil.transpose(Image.ROTATE_90)
    
    # Mantengamos la lógica consistente:
    # 1. Procesar grid tal cual llega par colorear
    # 2. Transponer imagen al final si se pide
    
    # IMPORTANTE: landxml2image hacía grid = grid_z.T
    # Si hacemos eso, cambiamos las dimensiones.
    # Vamos a asumir que el grid que entra aquí es grid_z tal cual sale de rasterize.
    
    # Para colorear, necesitamos normalizar.
    grid_to_plot = grid.T # Transponemos para que coincida con la lógica visual de landxml2image anterior
    height, width = grid_to_plot.shape
    valid = ~np.isnan(grid_to_plot)
    
    # Filtrado de ruido numérico (epsilon = 1mm)
    EPSILON = 1e-3
    grid_filtered = np.where(np.abs(grid_to_plot) < EPSILON, 0.0, grid_to_plot)
    
    # Clasificación
    if class_interval is not None and class_interval > 0:
        if center_zero:
            # Discretización simétrica respecto al cero
            grid_to_plot_vals = np.sign(grid_filtered) * np.floor(np.abs(grid_filtered) / class_interval) * class_interval
            # Limpiar -0.0 -> 0.0
            grid_to_plot_vals = np.where(np.abs(grid_to_plot_vals) < EPSILON, 0.0, grid_to_plot_vals)
        else:
             grid_to_plot_vals = np.floor(grid_filtered / class_interval) * class_interval
    else:
        grid_to_plot_vals = grid_filtered

    # Normalización y Color
    vmin, vmax = np.nanmin(grid_to_plot), np.nanmax(grid_to_plot)
    
    if center_zero:
        abs_max = max(abs(vmin), abs(vmax))
        norm = mcolors.TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)
    else:
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        
    cmap = plt.get_cmap(colormap)
    colored = cmap(norm(grid_to_plot_vals))
    
    # Blanqueamiento
    rgb = colored[:, :, :3]
    if whitening > 0:
        whitening = max(0.0, min(1.0, whitening))
        rgb = rgb * (1 - whitening) + whitening
    
    # Aplicar hillshade (después del blanqueamiento)
    if hillshade:
        from landxml_tools.processing.raster import calculate_hillshade
        hs = calculate_hillshade(grid_to_plot, hillshade_azimuth, hillshade_altitude, resolution=resolution)
        # Expandir hillshade a 3 canales
        hs_valid = np.nan_to_num(hs, nan=1.0)  # NaN -> 1.0 (sin sombra)
        hs_rgb = np.stack([hs_valid, hs_valid, hs_valid], axis=2)
        # Blend: modula luminosidad multiplicando el color por el hillshade
        # A mayor intensidad, más influencia del sombreado
        hillshade_intensity = max(0.0, min(1.0, hillshade_intensity))
        # Fórmula: rgb_final = rgb * (1 - intensity * (1 - hillshade))
        # Cuando hillshade=1 (luz directa): rgb sin cambios
        # Cuando hillshade=0 (sombra): rgb oscurecido según intensidad
        shading_factor = 1.0 - hillshade_intensity * (1.0 - hs_rgb)
        rgb = rgb * shading_factor
        rgb = np.clip(rgb, 0, 1)
        print(f"  Hillshade aplicado: azimut={hillshade_azimuth}°, altitud={hillshade_altitude}°, intensidad={hillshade_intensity*100:.0f}%")
        
    img_array = (rgb * 255).astype(np.uint8)
    
    # Crear imagen PNG (con alpha)
    img_pil_png = None
    if save_png:
        alpha = np.ones((height, width), dtype=np.uint8) * 255
        alpha[~valid] = 0
        img_rgba = np.dstack((img_array, alpha))
        img_pil_png = Image.fromarray(img_rgba, mode='RGBA')
        if rotate_90:
            img_pil_png = img_pil_png.transpose(Image.ROTATE_90)
        img_pil_png.save(png_path)
        print(f"  PNG guardado → {png_path}")

    # Crear imagen JPG (fondo blanco)
    if save_jpg:
        img_array[~valid] = 255 # Fondo blanco
        img_pil_jpg = Image.fromarray(img_array, mode='RGB')
        if rotate_90:
             img_pil_jpg = img_pil_jpg.transpose(Image.ROTATE_90)
        img_pil_jpg.save(jpg_path, "JPEG", quality=95)
        print(f"  JPG guardado → {jpg_path}")
