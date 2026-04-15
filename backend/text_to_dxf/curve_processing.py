"""
Curve Processing Module for DXF Generation

Extends the basic text_to_dxf processing to support:
- B-Spline curves (type S)
- NURBS curves (type N)
- Bezier curves (type B)
- Ellipses and elliptical arcs (type E)
- Polylines with curved segments (type PW)

Uses ezdxf's native spline support for mathematically accurate curve representation.
"""

import math
from typing import List, Tuple, Dict, Any, Optional
import ezdxf
from ezdxf.math import Vec3


def add_spline_to_modelspace(
    msp,
    control_points: List[Tuple[float, float]],
    degree: int = 3,
    knots: Optional[List[float]] = None,
    fit_points: Optional[List[Tuple[float, float]]] = None,
    closed: bool = False,
    layer: str = "0"
) -> None:
    """
    Add a B-Spline curve to the modelspace.

    Args:
        msp: ezdxf modelspace object
        control_points: List of (x, y) control point coordinates
        degree: Spline degree (default 3 for cubic)
        knots: Optional knot vector
        fit_points: Optional points the curve should interpolate
        closed: Whether to create a closed spline
        layer: Layer name
    """
    # Convert to 3D points (z=0)
    points_3d = [(x, y, 0) for x, y in control_points]

    if fit_points:
        # Create spline from fit points (interpolating spline)
        fit_3d = [(x, y, 0) for x, y in fit_points]
        spline = msp.add_spline(
            fit_points=fit_3d,
            degree=degree,
            dxfattribs={'layer': layer}
        )
    else:
        # Create spline from control points
        spline = msp.add_spline(dxfattribs={'layer': layer})
        spline.set_control_points(points_3d)
        spline.dxf.degree = degree

        if knots:
            spline.knots = knots

    if closed:
        spline.close()


def add_nurbs_to_modelspace(
    msp,
    control_points: List[Tuple[float, float]],
    weights: List[float],
    degree: int = 3,
    knots: Optional[List[float]] = None,
    layer: str = "0"
) -> None:
    """
    Add a NURBS (rational B-Spline) curve to the modelspace.

    Args:
        msp: ezdxf modelspace object
        control_points: List of (x, y) control point coordinates
        weights: List of weights for each control point
        degree: Curve degree
        knots: Optional knot vector
        layer: Layer name

    Mathematical Note:
    NURBS curve: C(u) = sum(N_i,p(u) * w_i * P_i) / sum(N_i,p(u) * w_i)
    where N_i,p are B-spline basis functions and w_i are weights.
    """
    # Convert to 3D points
    points_3d = [(x, y, 0) for x, y in control_points]

    # Use add_rational_spline for NURBS
    spline = msp.add_rational_spline(
        control_points=points_3d,
        weights=weights,
        degree=degree,
        knots=knots,
        dxfattribs={'layer': layer}
    )


def add_bezier_to_modelspace(
    msp,
    control_points: List[Tuple[float, float]],
    layer: str = "0",
    samples: int = 50
) -> None:
    """
    Add a Bezier curve to the modelspace.

    Since DXF doesn't have a native Bezier entity, we convert to a spline
    or sample the curve as a polyline.

    For degree <= 3, we can use exact spline representation.
    For higher degrees, we sample the curve.

    Args:
        msp: ezdxf modelspace object
        control_points: List of (x, y) control points
        layer: Layer name
        samples: Number of sample points for polyline fallback
    """
    n = len(control_points)
    degree = n - 1

    if degree <= 3:
        # Convert Bezier to B-Spline (exact for degree <= 3)
        # Bezier is a special case of B-Spline with specific knot vector
        points_3d = [(x, y, 0) for x, y in control_points]

        # Bezier knot vector: [0]*{degree+1}, [1]*{degree+1}
        knots = [0.0] * (degree + 1) + [1.0] * (degree + 1)

        spline = msp.add_spline(dxfattribs={'layer': layer})
        spline.set_control_points(points_3d)
        spline.dxf.degree = degree
        spline.knots = knots
    else:
        # Sample the Bezier curve and create polyline
        points = sample_bezier(control_points, samples)
        points_3d = [(x, y, 0, 0, 0) for x, y in points]  # x, y, start_width, end_width, bulge
        msp.add_lwpolyline(points_3d, dxfattribs={'layer': layer})


def sample_bezier(
    control_points: List[Tuple[float, float]],
    num_samples: int = 50
) -> List[Tuple[float, float]]:
    """
    Sample a Bezier curve using de Casteljau's algorithm.

    Mathematical basis:
    B(t) = sum_{i=0}^{n} C(n,i) * (1-t)^(n-i) * t^i * P_i

    de Casteljau's algorithm computes this recursively for numerical stability.
    """
    def de_casteljau(points: List[Tuple[float, float]], t: float) -> Tuple[float, float]:
        """Evaluate Bezier at parameter t using de Casteljau."""
        pts = list(points)
        n = len(pts)
        for r in range(1, n):
            for i in range(n - r):
                x = (1 - t) * pts[i][0] + t * pts[i + 1][0]
                y = (1 - t) * pts[i][1] + t * pts[i + 1][1]
                pts[i] = (x, y)
        return pts[0]

    samples = []
    for i in range(num_samples):
        t = i / (num_samples - 1)
        samples.append(de_casteljau(control_points, t))
    return samples


def add_ellipse_to_modelspace(
    msp,
    center: Tuple[float, float],
    major_axis: Tuple[float, float],
    ratio: float,
    start_param: float = 0.0,
    end_param: float = 2 * math.pi,
    layer: str = "0"
) -> None:
    """
    Add an ellipse or elliptical arc to the modelspace.

    Args:
        msp: ezdxf modelspace object
        center: (x, y) center coordinates
        major_axis: (dx, dy) major axis vector from center
        ratio: minor/major axis ratio (0 < ratio <= 1)
        start_param: Start parameter in radians
        end_param: End parameter in radians
        layer: Layer name

    Mathematical representation:
    Point at parameter t:
    x(t) = center_x + major_x * cos(t) - minor_x * sin(t)
    y(t) = center_y + major_y * cos(t) - minor_y * sin(t)
    where minor = ratio * major rotated 90 degrees
    """
    # ezdxf ellipse takes center, major_axis as 3D vectors
    center_3d = (center[0], center[1], 0)
    major_3d = (major_axis[0], major_axis[1], 0)

    msp.add_ellipse(
        center=center_3d,
        major_axis=major_3d,
        ratio=ratio,
        start_param=start_param,
        end_param=end_param,
        dxfattribs={'layer': layer}
    )


def add_polyline_with_curves_to_modelspace(
    msp,
    vertices: List[Dict[str, Any]],
    closed: bool = False,
    layer: str = "0"
) -> None:
    """
    Add a polyline with curved segments (bulge values) to the modelspace.

    Args:
        msp: ezdxf modelspace object
        vertices: List of vertex dicts with keys: x, y, bulge (optional),
                  start_width (optional), end_width (optional)
        closed: Whether to close the polyline
        layer: Layer name

    Bulge Mathematical Definition:
    bulge = tan(included_angle / 4)

    The bulge value defines an arc segment to the next vertex:
    - bulge = 0: Straight line segment
    - bulge > 0: Arc curves counter-clockwise (left)
    - bulge < 0: Arc curves clockwise (right)
    - |bulge| = 1: Semicircle (included_angle = 180 degrees)
    - |bulge| = tan(90/4) ≈ 0.414: Quarter circle (90 degrees)
    """
    # Convert to ezdxf format: (x, y, start_width, end_width, bulge)
    points = []
    for v in vertices:
        # Handle both dict and object (Pydantic model) formats
        if isinstance(v, dict):
            x = v['x']
            y = v['y']
            sw = v.get('start_width', 0)
            ew = v.get('end_width', 0)
            bulge = v.get('bulge', 0)
        else:
            x = getattr(v, 'x', 0)
            y = getattr(v, 'y', 0)
            sw = getattr(v, 'start_width', 0)
            ew = getattr(v, 'end_width', 0)
            bulge = getattr(v, 'bulge', 0)
        points.append((x, y, sw, ew, bulge))

    polyline = msp.add_lwpolyline(points, dxfattribs={'layer': layer})
    if closed:
        polyline.close()


def calculate_bulge_from_arc(
    start: Tuple[float, float],
    end: Tuple[float, float],
    center: Tuple[float, float]
) -> float:
    """
    Calculate bulge value from arc geometry.

    Given start point, end point, and center, calculate the bulge
    for a polyline segment.

    Mathematical derivation:
    1. Calculate the included angle from start to end around center
    2. bulge = tan(angle / 4)
    3. Sign determined by direction (CCW = positive)
    """
    # Vectors from center to points
    v1 = (start[0] - center[0], start[1] - center[1])
    v2 = (end[0] - center[0], end[1] - center[1])

    # Angles
    angle1 = math.atan2(v1[1], v1[0])
    angle2 = math.atan2(v2[1], v2[0])

    # Included angle (CCW positive)
    included = angle2 - angle1
    if included < 0:
        included += 2 * math.pi

    # Bulge
    bulge = math.tan(included / 4)

    # Check if arc is clockwise by cross product
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    if cross < 0:
        bulge = -bulge

    return bulge


def calculate_arc_from_bulge(
    start: Tuple[float, float],
    end: Tuple[float, float],
    bulge: float
) -> Dict[str, Any]:
    """
    Calculate arc geometry from bulge value.

    Returns center, radius, start_angle, end_angle for the arc.

    Mathematical derivation:
    1. included_angle = 4 * atan(bulge)
    2. sagitta = |bulge| * chord_length / 2
    3. radius = (chord_length^2 / 4 + sagitta^2) / (2 * sagitta)
    """
    if abs(bulge) < 1e-10:
        return None  # Straight line

    # Chord vector and length
    chord_x = end[0] - start[0]
    chord_y = end[1] - start[1]
    chord_length = math.sqrt(chord_x**2 + chord_y**2)

    if chord_length < 1e-10:
        return None

    # Included angle
    included = 4 * math.atan(abs(bulge))

    # Sagitta (arc height)
    sagitta = abs(bulge) * chord_length / 2

    # Radius
    radius = (chord_length**2 / 4 + sagitta**2) / (2 * sagitta)

    # Midpoint of chord
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2

    # Perpendicular unit vector
    perp_x = -chord_y / chord_length
    perp_y = chord_x / chord_length

    # Distance from midpoint to center
    h = radius - sagitta

    # Center (direction depends on bulge sign)
    if bulge > 0:
        center_x = mid_x + perp_x * h
        center_y = mid_y + perp_y * h
    else:
        center_x = mid_x - perp_x * h
        center_y = mid_y - perp_y * h

    # Start and end angles
    start_angle = math.atan2(start[1] - center_y, start[0] - center_x)
    end_angle = math.atan2(end[1] - center_y, end[0] - center_x)

    return {
        'center': (center_x, center_y),
        'radius': radius,
        'start_angle': math.degrees(start_angle),
        'end_angle': math.degrees(end_angle),
        'included_angle': math.degrees(included)
    }


def create_smooth_curve_through_points(
    points: List[Tuple[float, float]],
    method: str = "bspline",
    degree: int = 3,
    tension: float = 0.5
) -> Dict[str, Any]:
    """
    Create a smooth curve passing through given points.

    Args:
        points: List of (x, y) points to interpolate
        method: "bspline", "bezier", or "catmull_rom"
        degree: Curve degree for B-spline
        tension: Tension parameter for Catmull-Rom (0 = Catmull-Rom, 1 = tight)

    Returns:
        Dictionary with curve type and parameters ready for DXF generation
    """
    n = len(points)
    if n < 2:
        raise ValueError("Need at least 2 points")

    if method == "bspline":
        # For B-spline interpolation, we need to solve for control points
        # This is a simplified version - for production, use scipy or numpy
        return {
            'type': 'S',
            'fit_points': points,
            'degree': min(degree, n - 1)
        }

    elif method == "bezier":
        if n == 2:
            return {'type': 'B', 'control_points': points}
        elif n == 3:
            # Quadratic Bezier passes through middle point if it's the control point
            return {'type': 'B', 'control_points': points}
        else:
            # For more points, create composite Bezier or use B-spline
            return {
                'type': 'S',
                'fit_points': points,
                'degree': 3
            }

    elif method == "catmull_rom":
        # Catmull-Rom spline: passes through all points
        # Convert to cubic Bezier segments
        bezier_segments = []

        for i in range(n - 1):
            # Get 4 points for Catmull-Rom calculation
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[min(n - 1, i + 2)]

            # Convert to cubic Bezier control points
            # Using Catmull-Rom to Bezier conversion
            t = tension
            cp1 = (
                p1[0] + (p2[0] - p0[0]) / (6 * (1 - t)),
                p1[1] + (p2[1] - p0[1]) / (6 * (1 - t))
            )
            cp2 = (
                p2[0] - (p3[0] - p1[0]) / (6 * (1 - t)),
                p2[1] - (p3[1] - p1[1]) / (6 * (1 - t))
            )

            bezier_segments.append({
                'control_points': [p1, cp1, cp2, p2]
            })

        return {
            'type': 'bezier_segments',
            'segments': bezier_segments
        }

    return {'type': 'S', 'fit_points': points, 'degree': 3}


def process_curve_entity(
    msp,
    entity_type: str,
    data: Dict[str, Any],
    layer: str = "0"
) -> None:
    """
    Process a curve entity and add it to the modelspace.

    Args:
        msp: ezdxf modelspace object
        entity_type: One of 'S', 'N', 'B', 'E', 'PW'
        data: Entity data dictionary
        layer: Layer name
    """
    if entity_type == 'S':  # Spline
        add_spline_to_modelspace(
            msp,
            control_points=data.get('control_points', []),
            degree=data.get('degree', 3),
            knots=data.get('knots'),
            fit_points=data.get('fit_points'),
            closed=data.get('closed', False),
            layer=layer
        )

    elif entity_type == 'N':  # NURBS
        points = data.get('control_points', [])
        weights = data.get('weights', [1.0] * len(points))
        add_nurbs_to_modelspace(
            msp,
            control_points=points,
            weights=weights,
            degree=data.get('degree', 3),
            knots=data.get('knots'),
            layer=layer
        )

    elif entity_type == 'B':  # Bezier
        add_bezier_to_modelspace(
            msp,
            control_points=data.get('control_points', []),
            layer=layer
        )

    elif entity_type == 'E':  # Ellipse
        add_ellipse_to_modelspace(
            msp,
            center=(data['center_x'], data['center_y']),
            major_axis=(data['major_axis_x'], data['major_axis_y']),
            ratio=data.get('ratio', 1.0),
            start_param=data.get('start_param', 0),
            end_param=data.get('end_param', 2 * math.pi),
            layer=layer
        )

    elif entity_type == 'PW':  # Polyline with curves
        add_polyline_with_curves_to_modelspace(
            msp,
            vertices=data.get('vertices', []),
            closed=data.get('closed', False),
            layer=layer
        )
