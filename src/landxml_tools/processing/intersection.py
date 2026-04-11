"""
Motor de intersección de superficies LandXML 3D.

Calcula las curvas de intersección entre dos superficies TIN (2.5D) y las
exporta como polilíneas 3D en formato DXF.

Algoritmo:   Guigue-Devillers (intersección triángulo-triángulo)
Aceleración: cKDTree 2D (broad phase)
Topología:   Grafo de adyacencia con epsilon-quantization

Uso como librería:
    from landxml_tools.processing.intersection import resolver_interseccion
    resumen = resolver_interseccion(archivo_a, archivo_b, salida_dxf, epsilon=0.001)

Uso desde CLI:
    python -m landxml_tools.processing.intersection --input-a ... --input-b ... --output ...
"""

import os
import sys
import argparse
import numpy as np
from scipy.spatial import cKDTree
import ezdxf
from typing import Callable, Dict, List, Optional, Set, Tuple

# Reutilizar el parser robusto de landxml_tools (soporta LandXML 1.0, 1.1, 1.2)
from ..io.landxml import parse_landxml_surface


# =============================================================================
# Shift al origen (estabilidad numérica)
# =============================================================================

def _compute_offset(pts_a: np.ndarray, pts_b: np.ndarray) -> np.ndarray:
    """Calcula el vector mínimo XYZ de ambas superficies para trasladar al origen."""
    all_pts = np.vstack([pts_a, pts_b])
    return all_pts.min(axis=0)


def _apply_offset(pts: np.ndarray, offset: np.ndarray) -> np.ndarray:
    return pts - offset


def _remove_offset(pts: np.ndarray, offset: np.ndarray) -> np.ndarray:
    return pts + offset


# =============================================================================
# Broad Phase: cKDTree 2D
# =============================================================================

def _build_bboxes(pts: np.ndarray, faces: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calcula centros y semiejes 2D de los bounding boxes de cada triángulo."""
    n = len(faces)
    centers = np.zeros((n, 2))
    half_ext = np.zeros((n, 2))
    for i, face in enumerate(faces):
        xy = pts[face, :2]
        mn, mx = xy.min(axis=0), xy.max(axis=0)
        centers[i] = (mn + mx) / 2
        half_ext[i] = (mx - mn) / 2
    return centers, half_ext


def _boxes_overlap_2d(xy_a: np.ndarray, xy_b: np.ndarray, eps: float) -> bool:
    mna, mxa = xy_a.min(axis=0), xy_a.max(axis=0)
    mnb, mxb = xy_b.min(axis=0), xy_b.max(axis=0)
    return (mxa[0] >= mnb[0] - eps and mxb[0] >= mna[0] - eps and
            mxa[1] >= mnb[1] - eps and mxb[1] >= mna[1] - eps)


def _broad_phase(pts_a, faces_a, pts_b, faces_b, eps: float,
                 log_fn: Callable = print) -> List[Tuple[int, int]]:
    """
    Identifica pares candidatos de triángulos mediante un índice KDTree 2D.

    Returns:
        Lista de tuplas (idx_a, idx_b) para la fase narrow.
    """
    log_fn("[Broad Phase] Construyendo índice espacial...")
    centers_a, half_a = _build_bboxes(pts_a, faces_a)
    centers_b, half_b = _build_bboxes(pts_b, faces_b)

    tree = cKDTree(centers_a)
    candidates = []

    for i, (cb, hb) in enumerate(zip(centers_b, half_b)):
        radius = np.hypot(hb[0], hb[1]) * 2 + eps * 10
        nearby = tree.query_ball_point(cb, radius)
        for j in nearby:
            if _boxes_overlap_2d(pts_a[faces_a[j], :2], pts_b[faces_b[i], :2], eps):
                candidates.append((j, i))

    log_fn(f"  Candidatos: {len(candidates)}")
    return candidates


# =============================================================================
# Narrow Phase: Intersección triángulo-triángulo
# =============================================================================

def _line_triangle_isect(p1: np.ndarray, p2: np.ndarray,
                          tri: np.ndarray, eps: float) -> Optional[np.ndarray]:
    """Intersección de segmento p1→p2 con el triángulo tri (3×3)."""
    normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
    denom = np.dot(normal, p2 - p1)
    if abs(denom) < eps:
        return None
    t = np.dot(normal, tri[0] - p1) / denom
    if not (0.0 <= t <= 1.0):
        return None
    pt = p1 + t * (p2 - p1)
    # Coordenadas baricéntricas
    v0 = tri[2] - tri[0]
    v1 = tri[1] - tri[0]
    v2 = pt - tri[0]
    d00, d01, d02 = np.dot(v0, v0), np.dot(v0, v1), np.dot(v0, v2)
    d11, d12 = np.dot(v1, v1), np.dot(v1, v2)
    inv = d00 * d11 - d01 * d01
    if abs(inv) < eps:
        return None
    u = (d11 * d02 - d01 * d12) / inv
    v = (d00 * d12 - d01 * d02) / inv
    if u >= -eps and v >= -eps and u + v <= 1.0 + eps:
        return pt
    return None


def _tri_tri_isect(tri_a: np.ndarray, tri_b: np.ndarray,
                   eps: float = 1e-9) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Calcula el segmento de intersección entre dos triángulos 3D.

    Returns:
        Tupla (P1, P2) de extremos del segmento, o None si no hay intersección.
    """
    # Comprobar coplanaridad
    normal_a = np.cross(tri_a[1] - tri_a[0], tri_a[2] - tri_a[0])
    norm_len = np.linalg.norm(normal_a)
    if norm_len < eps:
        return None
    normal_a /= norm_len
    dists = [abs(np.dot(tri_b[k] - tri_a[0], normal_a)) for k in range(3)]
    if all(d < eps for d in dists):
        return None  # Coplanares: omitir

    pts = []
    edges_a = [(tri_a[0], tri_a[1]), (tri_a[1], tri_a[2]), (tri_a[2], tri_a[0])]
    edges_b = [(tri_b[0], tri_b[1]), (tri_b[1], tri_b[2]), (tri_b[2], tri_b[0])]

    for p1, p2 in edges_a:
        pt = _line_triangle_isect(p1, p2, tri_b, eps)
        if pt is not None:
            if not any(np.linalg.norm(pt - q) < eps for q in pts):
                pts.append(pt)

    for p1, p2 in edges_b:
        pt = _line_triangle_isect(p1, p2, tri_a, eps)
        if pt is not None:
            if not any(np.linalg.norm(pt - q) < eps for q in pts):
                pts.append(pt)

    if len(pts) < 2:
        return None

    # Tomar los dos extremos más alejados
    best, best_d = (pts[0], pts[1]), 0.0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = np.linalg.norm(pts[i] - pts[j])
            if d > best_d:
                best_d, best = d, (pts[i], pts[j])

    if best_d < 1e-4:
        return None

    return best


def _narrow_phase(pts_a, faces_a, pts_b, faces_b, candidates,
                  eps: float, log_fn: Callable = print) -> List[Tuple[np.ndarray, np.ndarray]]:
    log_fn("[Narrow Phase] Calculando intersecciones triángulo-triángulo...")
    segments = []
    for idx_a, idx_b in candidates:
        ta = pts_a[faces_a[idx_a]]
        tb = pts_b[faces_b[idx_b]]
        result = _tri_tri_isect(ta, tb, eps)
        if result is not None:
            segments.append(result)
    log_fn(f"  Segmentos: {len(segments)}")
    return segments


# =============================================================================
# Ensamblado topológico (Epsilon-Quantization)
# =============================================================================

def _quantize(pt: np.ndarray, eps: float) -> Tuple[int, int, int]:
    return (int(round(pt[0] / eps)), int(round(pt[1] / eps)), int(round(pt[2] / eps)))


def _dequantize(key: Tuple[int, int, int], eps: float) -> np.ndarray:
    return np.array([key[0] * eps, key[1] * eps, key[2] * eps])


def _build_adjacency(segments: List[Tuple[np.ndarray, np.ndarray]],
                     eps: float) -> Dict:
    adj: Dict[Tuple, List[Tuple]] = {}
    for p1, p2 in segments:
        k1, k2 = _quantize(p1, eps), _quantize(p2, eps)
        adj.setdefault(k1, []).append(k2)
        adj.setdefault(k2, []).append(k1)
    return adj


def _assemble_polylines(adj: Dict, eps: float,
                        log_fn: Callable = print) -> List[List[np.ndarray]]:
    log_fn("[Topología] Ensamblando polilíneas...")
    polylines = []
    visited: Set[Tuple] = set()

    for start in adj:
        if start in visited:
            continue
        unvisited_nbrs = [n for n in adj[start] if n not in visited]
        if not unvisited_nbrs:
            visited.add(start)
            continue

        for nxt in unvisited_nbrs:
            if nxt in visited:
                continue
            pline = [_dequantize(start, eps)]
            cur, tgt = start, nxt

            while True:
                visited.add(cur)
                pline.append(_dequantize(cur, eps))
                cur = tgt
                unv = [n for n in adj.get(cur, []) if n not in visited]
                if not unv:
                    break
                tgt = unv[0]

            if len(pline) >= 2:
                polylines.append(pline)

        visited.add(start)

    log_fn(f"  Polilíneas: {len(polylines)}")
    return polylines


# =============================================================================
# Exportación DXF
# =============================================================================

def _export_dxf(polylines: List[List[np.ndarray]], output_path: str,
                offset: np.ndarray, log_fn: Callable = print) -> int:
    """
    Exporta las polilíneas al archivo DXF, aplicando el offset inverso.

    Returns:
        Número de polilíneas exportadas.
    """
    log_fn("[Exportación] Generando archivo DXF...")
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    count = 0

    for pline in polylines:
        if len(pline) < 2:
            continue
        pts_global = [tuple(float(x) for x in _remove_offset(pt.reshape(1, 3), offset)[0])
                      for pt in pline]
        msp.add_polyline3d(pts_global)
        count += 1

    doc.saveas(output_path)
    log_fn(f"  Guardado: {output_path} ({count} polilíneas)")
    return count


# =============================================================================
# API pública
# =============================================================================

def resolver_interseccion(
    input_a: str,
    input_b: str,
    output_path: str,
    epsilon: float = 0.001,
    log_fn: Callable = print
) -> Dict:
    """
    Función principal del motor de intersección.

    Coordina todo el pipeline: parseo → shift → broad phase → narrow phase →
    ensamblado topológico → exportación DXF.

    Args:
        input_a:     Ruta al primer archivo LandXML.
        input_b:     Ruta al segundo archivo LandXML.
        output_path: Ruta de salida del archivo DXF.
        epsilon:     Tolerancia de quantization (por defecto 0.001 m).
        log_fn:      Función de logging (por defecto print; pasar una señal Qt en GUI).

    Returns:
        Diccionario con resumen: triangulos_a, triangulos_b, candidatos,
        segmentos, polilineas, output.
    """
    log_fn("=" * 60)
    log_fn("Motor de Intersección LandXML")
    log_fn(f"Epsilon: {epsilon}")
    log_fn("=" * 60)

    # --- Parseo ---
    log_fn("\n[1/6] Parseando archivos LandXML...")
    pts_a, faces_a = parse_landxml_surface(input_a)
    pts_b, faces_b = parse_landxml_surface(input_b)

    if faces_a is None or len(faces_a) == 0:
        raise ValueError(f"No se encontraron triángulos en {input_a}")
    if faces_b is None or len(faces_b) == 0:
        raise ValueError(f"No se encontraron triángulos en {input_b}")

    log_fn(f"  Superficie A: {len(faces_a)} triángulos")
    log_fn(f"  Superficie B: {len(faces_b)} triángulos")

    # --- Shift al origen ---
    log_fn("\n[2/6] Aplicando shift al origen...")
    offset = _compute_offset(pts_a, pts_b)
    log_fn(f"  Offset: X={offset[0]:.3f}, Y={offset[1]:.3f}, Z={offset[2]:.3f}")
    pts_a_l = _apply_offset(pts_a, offset)
    pts_b_l = _apply_offset(pts_b, offset)

    # --- Broad Phase ---
    log_fn("\n[3/6] Broad Phase (cKDTree 2D)...")
    candidates = _broad_phase(pts_a_l, faces_a, pts_b_l, faces_b, epsilon, log_fn)

    resumen = {
        "triangulos_a": len(faces_a),
        "triangulos_b": len(faces_b),
        "candidatos":   len(candidates),
        "segmentos":    0,
        "polilineas":   0,
        "output":       output_path,
    }

    # --- Narrow Phase ---
    log_fn("\n[4/6] Narrow Phase (Guigue-Devillers)...")
    segments = _narrow_phase(pts_a_l, faces_a, pts_b_l, faces_b, candidates, epsilon, log_fn)
    resumen["segmentos"] = len(segments)

    if not segments:
        log_fn("\n[AVISO] No se encontraron intersecciones.")
        ezdxf.new('R2010').saveas(output_path)
        return resumen

    # --- Ensamblado ---
    log_fn("\n[5/6] Ensamblado topológico...")
    adj = _build_adjacency(segments, epsilon)
    polylines = _assemble_polylines(adj, epsilon, log_fn)

    # --- Exportación ---
    log_fn("\n[6/6] Exportación DXF...")
    resumen["polilineas"] = _export_dxf(polylines, output_path, offset, log_fn)

    log_fn("\n" + "=" * 60)
    log_fn(f"COMPLETADO: {resumen['polilineas']} polilíneas exportadas.")
    log_fn("=" * 60)
    return resumen


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Intersección de Superficies LandXML 3D',
        epilog='Ejemplo: python -m landxml_tools.processing.intersection '
               '--input-a a.xml --input-b b.xml --output resultado.dxf'
    )
    parser.add_argument('--input-a',  required=True)
    parser.add_argument('--input-b',  required=True)
    parser.add_argument('--output',   required=True)
    parser.add_argument('--epsilon',  type=float, default=0.001)
    args = parser.parse_args()

    res = resolver_interseccion(args.input_a, args.input_b, args.output, args.epsilon)
    print(f"\nResumen: {res['polilineas']} polilíneas en {res['output']}")


if __name__ == '__main__':
    main()
