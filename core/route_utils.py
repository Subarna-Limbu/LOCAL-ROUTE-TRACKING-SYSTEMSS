"""Utility helpers for route polyline operations (projection and cumulative distances).

This file provides light-weight functions to:
- compute cumulative distances along a polyline of (lat,lng) points
- project a lat/lng point to the polyline and compute distance along route

Note: This is a simple implementation using haversine distances and per-segment
vector projection on an equirectangular (approximate) plane. It's sufficient for
mid-range distances and can be replaced by shapely/turf-based map-matching later.
"""
from typing import List, Tuple, Optional
import math

def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def polyline_cumulative_distances(polyline: List[Tuple[float,float]]) -> List[float]:
    """Return cumulative distances (meters) for each vertex in the polyline.
    cumdist[0] == 0.0
    """
    cum = [0.0]
    for i in range(1, len(polyline)):
        a = polyline[i-1]
        b = polyline[i]
        d = haversine_meters(a[0], a[1], b[0], b[1])
        cum.append(cum[-1] + d)
    return cum


def project_point_on_segment(p: Tuple[float,float], a: Tuple[float,float], b: Tuple[float,float]) -> Tuple[float, Tuple[float,float]]:
    """Project point p onto segment a-b using equirectangular projection.
    Returns (t, proj_point) where t in [0,1] is fraction along a->b.
    """
    # choose reference latitude for scaling
    lat0 = math.radians((a[0] + b[0] + p[0]) / 3.0)
    kx = math.cos(lat0) * 111320.0  # meters per degree lon approx
    ky = 110540.0  # meters per degree lat approx
    ax = a[1] * kx
    ay = a[0] * ky
    bx = b[1] * kx
    by = b[0] * ky
    px = p[1] * kx
    py = p[0] * ky
    vx = bx - ax
    vy = by - ay
    wx = px - ax
    wy = py - ay
    denom = vx*vx + vy*vy
    if denom == 0:
        return 0.0, (a[0], a[1])
    t = (wx*vx + wy*vy) / denom
    t_clamped = max(0.0, min(1.0, t))
    proj_x = ax + t_clamped * vx
    proj_y = ay + t_clamped * vy
    proj_lon = proj_x / kx
    proj_lat = proj_y / ky
    return t_clamped, (proj_lat, proj_lon)


def project_point_onto_polyline(polyline: List[Tuple[float,float]], point: Tuple[float,float]) -> Optional[Tuple[int, float, float, Tuple[float,float]]]:
    """Project point onto polyline. Returns a tuple of:
    (segment_index, t_on_segment, distance_to_projection_m, projected_point_latlng)
    or None if polyline empty.
    """
    if not polyline:
        return None
    best = None
    for i in range(len(polyline)-1):
        a = polyline[i]
        b = polyline[i+1]
        t, proj = project_point_on_segment(point, a, b)
        d = haversine_meters(point[0], point[1], proj[0], proj[1])
        if best is None or d < best[2]:
            best = (i, t, d, proj)
    return best


def distance_along_polyline_to_projection(polyline: List[Tuple[float,float]], cumdist: List[float], segment_index: int, t: float) -> float:
    """Given cumulative distances and a projection (segment index and t),
    return the distance along the polyline from start to the projected point (meters).
    """
    if segment_index < 0:
        return 0.0
    if segment_index >= len(cumdist):
        return cumdist[-1]
    # distance to start of segment
    d0 = cumdist[segment_index]
    # length of segment
    a = polyline[segment_index]
    b = polyline[segment_index+1]
    seg_len = haversine_meters(a[0], a[1], b[0], b[1])
    return d0 + seg_len * max(0.0, min(1.0, t))
