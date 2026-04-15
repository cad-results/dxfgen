"""
Mathematical Core Module for DXF Generation

This module provides mathematically sound implementations for:
- Linear geometry (lines, polygons, polylines)
- Nonlinear curves (Bezier, B-Splines, NURBS)
- BRep (Boundary Representation) parameters
- Polynomial interpolation
- Geometric transformations
"""

from .curves import (
    BezierCurve,
    BSplineCurve,
    NURBSCurve,
    PolynomialInterpolator,
    ArcParameterization,
)

from .brep import (
    EdgeType,
    SurfaceType,
    Orientation,
    BRepVertex,
    BRepEdge,
    BRepFace,
    BRepLoop,
    BRepShell,
    BRepSolid,
    calculate_edge_parameters,
    calculate_surface_parameters,
    create_edge_from_points,
    polygon_to_loop,
)

from .geometry import (
    Point2D,
    Point3D,
    Vector2D,
    Vector3D,
    LineSegment,
    Polygon,
    compute_polygon_area,
    compute_centroid,
    point_in_polygon,
    offset_polygon,
)

__all__ = [
    # Curves
    'BezierCurve',
    'BSplineCurve',
    'NURBSCurve',
    'PolynomialInterpolator',
    'ArcParameterization',
    # BRep
    'EdgeType',
    'SurfaceType',
    'Orientation',
    'BRepVertex',
    'BRepEdge',
    'BRepFace',
    'BRepLoop',
    'BRepShell',
    'BRepSolid',
    'calculate_edge_parameters',
    'calculate_surface_parameters',
    'create_edge_from_points',
    'polygon_to_loop',
    # Geometry
    'Point2D',
    'Point3D',
    'Vector2D',
    'Vector3D',
    'LineSegment',
    'Polygon',
    'compute_polygon_area',
    'compute_centroid',
    'point_in_polygon',
    'offset_polygon',
]
