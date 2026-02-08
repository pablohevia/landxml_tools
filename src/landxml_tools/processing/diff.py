"""
Módulo para cálculo de diferencias entre superficies.
"""

import numpy as np
from .raster import rasterize_surface_tin

def calculate_difference(points1, triangles1, points2, triangles2, resolution=0.05):
    """
    Calcula la diferencia de elevación entre dos superficies TIN.
    
    Rasteriza ambas superficies en un grid común (la intersección de sus
    extensiones) y calcula superficie2 - superficie1 píxel a píxel.
    
    Args:
        points1 (ndarray): Puntos de la superficie base (n1, 3).
        triangles1 (ndarray): Triángulos de la superficie base (m1, 3).
        points2 (ndarray): Puntos de la superficie a comparar (n2, 3).
        triangles2 (ndarray): Triángulos de la superficie a comparar (m2, 3).
        resolution (float): Tamaño de píxel en metros. Por defecto 0.05 m.
    
    Returns:
        tuple: Una tupla (diff_grid, extent) donde:
            - diff_grid (ndarray): Array 2D con diferencias (sup2 - sup1).
              Valores positivos indican relleno, negativos indican corte.
              NaN donde alguna superficie no tiene datos.
            - extent (list): [xmin, xmax, ymin, ymax] de la extensión común.
    """
    # Calcular extensión común (intersección)
    xmin = max(points1[:, 0].min(), points2[:, 0].min())
    xmax = min(points1[:, 0].max(), points2[:, 0].max())
    ymin = max(points1[:, 1].min(), points2[:, 1].min())
    ymax = min(points1[:, 1].max(), points2[:, 1].max())
    
    # Ajustar para píxeles cuadrados
    xmax = xmin + np.ceil((xmax - xmin) / resolution) * resolution
    ymax = ymin + np.ceil((ymax - ymin) / resolution) * resolution
    
    extent = [xmin, xmax, ymin, ymax]
    
    print(f"\n  Extensión común:")
    print(f"    X: {xmin:.2f} → {xmax:.2f} ({xmax-xmin:.2f}m)")
    print(f"    Y: {ymin:.2f} → {ymax:.2f} ({ymax-ymin:.2f}m)")
    
    # Rasterizar ambas superficies en el grid común
    print(f"  Rasterizando superficie 1...")
    grid1, _ = rasterize_surface_tin(points1, triangles1, resolution=resolution, extent=extent)
    
    print(f"  Rasterizando superficie 2...")
    grid2, _ = rasterize_surface_tin(points2, triangles2, resolution=resolution, extent=extent)
    
    grid1 = np.asarray(grid1, dtype=float)
    grid2 = np.asarray(grid2, dtype=float)
    
    # Calcular diferencia solo donde ambos tienen datos
    mask = ~np.isnan(grid1) & ~np.isnan(grid2)
    diff_grid = np.full(grid1.shape, np.nan)
    diff_grid[mask] = grid2[mask] - grid1[mask]
    
    # Estadísticas
    valid_diff = diff_grid[mask]
    if len(valid_diff) > 0:
        print(f"\n  Estadísticas de diferencia:")
        print(f"    Píxeles válidos: {len(valid_diff)}")
        print(f"    Mínimo: {valid_diff.min():.3f} m (corte)")
        print(f"    Máximo: {valid_diff.max():.3f} m (relleno)")
        print(f"    Media:  {valid_diff.mean():.3f} m")
        print(f"    Mediana: {np.median(valid_diff):.3f} m")
        print(f"    Desv.Est: {valid_diff.std():.3f} m")
    
    return diff_grid, extent
