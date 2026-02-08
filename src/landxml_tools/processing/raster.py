"""
Módulo para rasterización de superficies TIN.
"""

import numpy as np
import matplotlib.tri as mtri
from .tin import validate_and_clean_triangulation

def rasterize_surface_tin(points, triangles, resolution=0.05, extent=None):
    """
    Rasteriza una superficie TIN a un grid regular.
    
    Args:
        points (ndarray): Array de forma (n, 3) con coordenadas [X, Y, Z].
        triangles (ndarray | None): Array de forma (m, 3) con índices de
            triángulos. Si es None, se intenta generar triangulación de Delaunay.
        resolution (float): Tamaño de píxel en metros. Por defecto 0.05 m.
        extent (list | None): [xmin, xmax, ymin, ymax]. Si es None, se calcula
            automáticamente a partir de los puntos.
    
    Returns:
        tuple: (grid_z, extent) donde:
            - grid_z (ndarray): Array 2D con elevaciones interpoladas.
            - extent (list): [xmin, xmax, ymin, ymax] ajustado al grid.
    """
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    
    if extent is None:
        xmin, xmax = float(x.min()), float(x.max())
        ymin, ymax = float(y.min()), float(y.max())
    else:
        xmin, xmax, ymin, ymax = extent

    # Ajustar para píxeles cuadrados
    # Importante: Esto puede expandir ligeramente el extent original
    xmax = xmin + np.ceil((xmax - xmin) / resolution) * resolution
    ymax = ymin + np.ceil((ymax - ymin) / resolution) * resolution

    # Calcular número exacto de píxeles
    num_pixels_x = int(np.round((xmax - xmin) / resolution))
    num_pixels_y = int(np.round((ymax - ymin) / resolution))
    
    # Crear arrays de coordenadas usando linspace para exactitud
    xi = np.linspace(xmin, xmax, num_pixels_x + 1)[:-1]
    yi = np.linspace(ymin, ymax, num_pixels_y + 1)[:-1]
    
    # Ajustar a centros de píxeles
    xi = xi + resolution / 2
    yi = yi + resolution / 2
    
    xi_grid, yi_grid = np.meshgrid(xi, yi)
    
    print(f"\nCreando grid: {num_pixels_x}x{num_pixels_y} píxeles")
    
    # Crear triangulación
    triang = None
    if triangles is not None:
        triangles_clean = validate_and_clean_triangulation(points, triangles)
        if triangles_clean is not None and len(triangles_clean) > 0:
            try:
                temp_triang = mtri.Triangulation(x, y, triangles_clean)
                _ = temp_triang.get_trifinder()
                triang = temp_triang
            except Exception as e:
                print(f"    ⚠ Triangulación original inválida: {e}")
                triang = None
    
    if triang is None:
        print("    ℹ Generando triangulación de Delaunay automática...")
        # Eliminar duplicados para Delaunay
        xy_points = np.column_stack((x, y))
        _, unique_indices = np.unique(xy_points, axis=0, return_index=True)
        
        if len(unique_indices) < len(x):
            x_clean = x[unique_indices]
            y_clean = y[unique_indices]
            z_clean = z[unique_indices]
            triang = mtri.Triangulation(x_clean, y_clean)
            z_used = z_clean
        else:
            triang = mtri.Triangulation(x, y)
            z_used = z
    else:
        z_used = z

    # Interpolación lineal
    try:
        interpolator = mtri.LinearTriInterpolator(triang, z_used)
        grid_z = interpolator(xi_grid, yi_grid)
    except Exception as e:
        print(f"    ❌ Error fatal en interpolación: {e}")
        return np.full(xi_grid.shape, np.nan), [xmin, xmax, ymin, ymax]
    
    # Convertir masked array a NaN
    if hasattr(grid_z, 'mask'):
        grid_z = np.ma.filled(grid_z, np.nan)
    
    return grid_z, [xmin, xmax, ymin, ymax]


def calculate_hillshade(grid_z, azimuth=315, altitude=45, resolution=1.0):
    """
    Calcula el sombreado de relieve (hillshade) a partir de un grid de elevaciones.
    
    Args:
        grid_z (numpy.ndarray): Grid 2D con elevaciones (puede contener NaN).
        azimuth (float): Ángulo del sol en grados (0=Norte, 90=Este, 315=Noroeste).
        altitude (float): Elevación del sol sobre el horizonte en grados (0-90).
        resolution (float): Tamaño de celda en metros (para escalar gradientes).
    
    Returns:
        numpy.ndarray: Grid 2D con valores de sombreado normalizados (0-1).
    """
    # Convertir ángulos a radianes (ajuste para convención cartográfica)
    azimuth_rad = np.radians(360 - azimuth + 90)
    altitude_rad = np.radians(altitude)
    
    # Calcular gradientes (pendientes) en X e Y
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
