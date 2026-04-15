"""
BRep (Boundary Representation) Module

Provides mathematically sound BRep data structures and calculations for:
- Edges (with curve geometry)
- Loops (closed sequences of edges)
- Faces (bounded regions with loops)
- Shells (connected faces)
- Solids (closed shells)

BRep is the standard representation in CAD systems for defining
3D shapes through their boundary surfaces and edges.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Union, Dict, Any
from enum import Enum
import numpy as np

from .geometry import Point2D, Point3D, Vector2D, Vector3D, LineSegment, Polygon
from .curves import BezierCurve, BSplineCurve, NURBSCurve


class EdgeType(Enum):
    """Types of edge geometry."""
    LINE = "line"
    ARC = "arc"
    CIRCLE = "circle"
    BEZIER = "bezier"
    BSPLINE = "bspline"
    NURBS = "nurbs"


class SurfaceType(Enum):
    """Types of surface geometry."""
    PLANE = "plane"
    CYLINDER = "cylinder"
    CONE = "cone"
    SPHERE = "sphere"
    TORUS = "torus"
    BEZIER_SURFACE = "bezier_surface"
    BSPLINE_SURFACE = "bspline_surface"
    NURBS_SURFACE = "nurbs_surface"


class Orientation(Enum):
    """Orientation of geometric elements."""
    FORWARD = "forward"
    REVERSED = "reversed"


@dataclass
class BRepVertex:
    """
    BRep Vertex - a point in 3D space.

    Vertices are the endpoints of edges and are shared between
    adjacent edges in a topologically correct model.
    """
    point: Point3D
    id: Optional[str] = None
    tolerance: float = 1e-6

    def distance_to(self, other: BRepVertex) -> float:
        """Distance to another vertex."""
        return self.point.distance_to(other.point)

    def coincident(self, other: BRepVertex) -> bool:
        """Check if vertices are coincident within tolerance."""
        return self.distance_to(other) < self.tolerance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "vertex",
            "id": self.id,
            "point": self.point.to_tuple(),
            "tolerance": self.tolerance
        }


@dataclass
class BRepEdge:
    """
    BRep Edge - a curve bounded by two vertices.

    Mathematical Properties:
    - Edge has a parametric curve representation
    - Parameter range [u_start, u_end] maps to vertices
    - Edge can be linear (line) or nonlinear (arc, spline, etc.)
    - Geometric continuity (G0, G1, G2) with adjacent edges

    BRep Parameters:
    - start_vertex, end_vertex: Topological endpoints
    - curve_type: Type of underlying geometry
    - curve_params: Parameters defining the curve
    - orientation: Whether parameter direction matches vertex order
    """
    start_vertex: BRepVertex
    end_vertex: BRepVertex
    curve_type: EdgeType = EdgeType.LINE
    curve_params: Dict[str, Any] = field(default_factory=dict)
    orientation: Orientation = Orientation.FORWARD
    id: Optional[str] = None
    tolerance: float = 1e-6

    # Cached curve object
    _curve: Optional[Union[LineSegment, BezierCurve, BSplineCurve, NURBSCurve]] = field(
        default=None, repr=False
    )

    def __post_init__(self):
        """Initialize curve geometry from parameters."""
        self._build_curve()

    def _build_curve(self):
        """Build curve object from type and parameters."""
        p1 = self.start_vertex.point.to_2d()
        p2 = self.end_vertex.point.to_2d()

        if self.curve_type == EdgeType.LINE:
            self._curve = LineSegment(p1, p2)

        elif self.curve_type == EdgeType.ARC:
            # Arc parameters: center, radius, start_angle, end_angle
            center = self.curve_params.get("center", Point2D(0, 0))
            radius = self.curve_params.get("radius", p1.distance_to(p2) / 2)
            start_angle = self.curve_params.get("start_angle", 0)
            end_angle = self.curve_params.get("end_angle", math.pi)

            # Create NURBS representation of arc
            self._curve = NURBSCurve.circle(center, radius, start_angle, end_angle)

        elif self.curve_type == EdgeType.BEZIER:
            control_points = self.curve_params.get("control_points", [p1, p2])
            self._curve = BezierCurve(control_points)

        elif self.curve_type == EdgeType.BSPLINE:
            control_points = self.curve_params.get("control_points", [p1, p2])
            degree = self.curve_params.get("degree", 3)
            knots = self.curve_params.get("knots", None)
            self._curve = BSplineCurve(control_points, degree, knots)

        elif self.curve_type == EdgeType.NURBS:
            control_points = self.curve_params.get("control_points", [p1, p2])
            weights = self.curve_params.get("weights", [1.0] * len(control_points))
            degree = self.curve_params.get("degree", 3)
            knots = self.curve_params.get("knots", None)
            self._curve = NURBSCurve(control_points, weights, degree, knots)

    @property
    def length(self) -> float:
        """Calculate edge length."""
        if isinstance(self._curve, LineSegment):
            return self._curve.length
        elif hasattr(self._curve, 'arc_length'):
            return self._curve.arc_length()
        elif hasattr(self._curve, 'sample'):
            points = self._curve.sample(100)
            return sum(
                points[i].distance_to(points[i + 1])
                for i in range(len(points) - 1)
            )
        return self.start_vertex.point.distance_to(self.end_vertex.point)

    def point_at(self, t: float) -> Point2D:
        """
        Get point at parameter t (0 <= t <= 1).

        Handles orientation: if reversed, t=0 returns end_vertex.
        """
        if self.orientation == Orientation.REVERSED:
            t = 1 - t

        if isinstance(self._curve, LineSegment):
            return self._curve.point_at(t)
        elif hasattr(self._curve, 'evaluate'):
            return self._curve.evaluate(t)
        else:
            # Fallback to linear interpolation
            p1 = self.start_vertex.point.to_2d()
            p2 = self.end_vertex.point.to_2d()
            return Point2D(
                p1.x + t * (p2.x - p1.x),
                p1.y + t * (p2.y - p1.y)
            )

    def tangent_at(self, t: float) -> Vector2D:
        """Get tangent vector at parameter t."""
        if self.orientation == Orientation.REVERSED:
            t = 1 - t

        if isinstance(self._curve, LineSegment):
            return self._curve.direction
        elif hasattr(self._curve, 'derivative'):
            return self._curve.derivative(t)
        else:
            # Numerical approximation
            dt = 0.001
            p1 = self.point_at(max(0, t - dt))
            p2 = self.point_at(min(1, t + dt))
            return (p2 - p1).normalize()

    def curvature_at(self, t: float) -> float:
        """Get curvature at parameter t."""
        if isinstance(self._curve, LineSegment):
            return 0.0
        elif hasattr(self._curve, 'curvature'):
            return self._curve.curvature(t)
        else:
            # Numerical approximation using three points
            dt = 0.01
            t0 = max(0, t - dt)
            t1 = t
            t2 = min(1, t + dt)

            p0 = self.point_at(t0)
            p1 = self.point_at(t1)
            p2 = self.point_at(t2)

            # Menger curvature: 4 * area / (|p0-p1| * |p1-p2| * |p2-p0|)
            area = abs((p1.x - p0.x) * (p2.y - p0.y) - (p2.x - p0.x) * (p1.y - p0.y)) / 2
            d01 = p0.distance_to(p1)
            d12 = p1.distance_to(p2)
            d20 = p2.distance_to(p0)

            denom = d01 * d12 * d20
            if denom < 1e-10:
                return 0.0

            return 4 * area / denom

    def sample(self, num_points: int = 50) -> List[Point2D]:
        """Sample edge at uniform parameter intervals."""
        return [self.point_at(i / (num_points - 1)) for i in range(num_points)]

    def reverse(self) -> BRepEdge:
        """Return a reversed copy of this edge."""
        new_orientation = (
            Orientation.REVERSED if self.orientation == Orientation.FORWARD
            else Orientation.FORWARD
        )
        return BRepEdge(
            start_vertex=self.end_vertex,
            end_vertex=self.start_vertex,
            curve_type=self.curve_type,
            curve_params=self.curve_params.copy(),
            orientation=new_orientation,
            id=self.id,
            tolerance=self.tolerance
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize edge to dictionary."""
        return {
            "type": "edge",
            "id": self.id,
            "curve_type": self.curve_type.value,
            "start_vertex": self.start_vertex.to_dict(),
            "end_vertex": self.end_vertex.to_dict(),
            "curve_params": self.curve_params,
            "orientation": self.orientation.value,
            "length": self.length
        }


@dataclass
class BRepLoop:
    """
    BRep Loop - a closed sequence of connected edges.

    A loop represents a boundary of a face. A face can have:
    - One outer loop (defines the face boundary)
    - Zero or more inner loops (define holes)

    Mathematical Properties:
    - Edges must form a closed chain (end of one = start of next)
    - Outer loops are typically oriented counter-clockwise
    - Inner loops (holes) are oriented clockwise
    """
    edges: List[BRepEdge]
    is_outer: bool = True
    id: Optional[str] = None

    def __post_init__(self):
        """Validate loop topology."""
        self._validate()

    def _validate(self):
        """Check that edges form a closed loop."""
        if len(self.edges) < 1:
            return

        for i in range(len(self.edges)):
            current_end = self.edges[i].end_vertex
            next_start = self.edges[(i + 1) % len(self.edges)].start_vertex

            if not current_end.coincident(next_start):
                raise ValueError(
                    f"Loop edges are not connected: edge {i} end != edge {(i+1) % len(self.edges)} start"
                )

    @property
    def vertices(self) -> List[BRepVertex]:
        """Get all vertices in loop order."""
        return [edge.start_vertex for edge in self.edges]

    @property
    def perimeter(self) -> float:
        """Calculate total perimeter of loop."""
        return sum(edge.length for edge in self.edges)

    def area(self) -> float:
        """
        Calculate enclosed area using the shoelace formula.

        For curved edges, this samples the curves.
        """
        # Sample all edges and compute polygon area
        all_points = []
        for edge in self.edges:
            points = edge.sample(20)
            all_points.extend(points[:-1])  # Avoid duplicating endpoints

        if len(all_points) < 3:
            return 0.0

        # Shoelace formula
        area = 0.0
        n = len(all_points)
        for i in range(n):
            j = (i + 1) % n
            area += all_points[i].x * all_points[j].y
            area -= all_points[j].x * all_points[i].y

        return abs(area) / 2.0

    def centroid(self) -> Point2D:
        """Calculate centroid of loop."""
        # Sample edges
        all_points = []
        for edge in self.edges:
            points = edge.sample(20)
            all_points.extend(points[:-1])

        if not all_points:
            return Point2D(0, 0)

        cx = sum(p.x for p in all_points) / len(all_points)
        cy = sum(p.y for p in all_points) / len(all_points)
        return Point2D(cx, cy)

    def contains_point(self, point: Point2D) -> bool:
        """Test if point is inside the loop using ray casting."""
        # Sample edges to create polygon
        all_points = []
        for edge in self.edges:
            points = edge.sample(20)
            all_points.extend(points[:-1])

        polygon = Polygon(all_points, closed=True)
        from .geometry import point_in_polygon
        return point_in_polygon(point, polygon)

    def to_polygon(self, samples_per_edge: int = 20) -> Polygon:
        """Convert loop to polygon by sampling edges."""
        all_points = []
        for edge in self.edges:
            points = edge.sample(samples_per_edge)
            all_points.extend(points[:-1])
        return Polygon(all_points, closed=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "loop",
            "id": self.id,
            "is_outer": self.is_outer,
            "edges": [e.to_dict() for e in self.edges],
            "perimeter": self.perimeter,
            "area": self.area()
        }


@dataclass
class BRepFace:
    """
    BRep Face - a bounded region defined by loops.

    A face represents a surface region bounded by one outer loop
    and zero or more inner loops (holes).

    Mathematical Properties:
    - Face has an underlying surface geometry
    - Outer loop defines the boundary
    - Inner loops define holes
    - Normal vector defines face orientation
    """
    outer_loop: BRepLoop
    inner_loops: List[BRepLoop] = field(default_factory=list)
    surface_type: SurfaceType = SurfaceType.PLANE
    surface_params: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

    def __post_init__(self):
        """Validate face topology."""
        if not self.outer_loop.is_outer:
            self.outer_loop.is_outer = True

        for loop in self.inner_loops:
            loop.is_outer = False

    @property
    def area(self) -> float:
        """Calculate face area (outer - holes)."""
        total = self.outer_loop.area()
        for inner in self.inner_loops:
            total -= inner.area()
        return max(0, total)

    @property
    def perimeter(self) -> float:
        """Total perimeter including holes."""
        total = self.outer_loop.perimeter
        for inner in self.inner_loops:
            total += inner.perimeter
        return total

    def centroid(self) -> Point2D:
        """Calculate face centroid."""
        return self.outer_loop.centroid()

    def contains_point(self, point: Point2D) -> bool:
        """Test if point is inside face (in outer but not in holes)."""
        if not self.outer_loop.contains_point(point):
            return False

        for inner in self.inner_loops:
            if inner.contains_point(point):
                return False

        return True

    def normal(self) -> Vector3D:
        """Get face normal vector."""
        if self.surface_type == SurfaceType.PLANE:
            # For planar faces, compute from vertices
            vertices = self.outer_loop.vertices
            if len(vertices) < 3:
                return Vector3D(0, 0, 1)

            p0 = vertices[0].point
            p1 = vertices[1].point
            p2 = vertices[2].point

            v1 = p1 - p0
            v2 = p2 - p0

            return v1.cross(v2).normalize()

        # For other surface types, use surface_params
        return self.surface_params.get("normal", Vector3D(0, 0, 1))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "face",
            "id": self.id,
            "surface_type": self.surface_type.value,
            "outer_loop": self.outer_loop.to_dict(),
            "inner_loops": [l.to_dict() for l in self.inner_loops],
            "area": self.area,
            "perimeter": self.perimeter
        }


@dataclass
class BRepShell:
    """
    BRep Shell - a collection of connected faces.

    A shell represents a connected boundary surface.
    - Open shell: has boundary edges (not all edges shared by two faces)
    - Closed shell: all edges shared by exactly two faces (watertight)
    """
    faces: List[BRepFace]
    is_closed: bool = False
    id: Optional[str] = None

    def __post_init__(self):
        """Check if shell is closed."""
        self.is_closed = self._check_closed()

    def _check_closed(self) -> bool:
        """Check if all edges are shared by exactly two faces."""
        edge_count: Dict[str, int] = {}

        for face in self.faces:
            for edge in face.outer_loop.edges:
                key = edge.id or id(edge)
                edge_count[key] = edge_count.get(key, 0) + 1

            for loop in face.inner_loops:
                for edge in loop.edges:
                    key = edge.id or id(edge)
                    edge_count[key] = edge_count.get(key, 0) + 1

        # Closed if all edges appear exactly twice
        return all(count == 2 for count in edge_count.values())

    @property
    def surface_area(self) -> float:
        """Total surface area of shell."""
        return sum(face.area for face in self.faces)

    @property
    def num_faces(self) -> int:
        return len(self.faces)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "shell",
            "id": self.id,
            "is_closed": self.is_closed,
            "faces": [f.to_dict() for f in self.faces],
            "surface_area": self.surface_area,
            "num_faces": self.num_faces
        }


@dataclass
class BRepSolid:
    """
    BRep Solid - a 3D region bounded by closed shells.

    A solid is defined by:
    - One outer shell (bounds the solid from outside)
    - Zero or more inner shells (define voids/cavities)
    """
    outer_shell: BRepShell
    inner_shells: List[BRepShell] = field(default_factory=list)
    id: Optional[str] = None

    def __post_init__(self):
        """Validate solid topology."""
        if not self.outer_shell.is_closed:
            raise ValueError("Outer shell must be closed for a valid solid")

        for shell in self.inner_shells:
            if not shell.is_closed:
                raise ValueError("Inner shells must be closed for a valid solid")

    @property
    def surface_area(self) -> float:
        """Total surface area including voids."""
        total = self.outer_shell.surface_area
        for inner in self.inner_shells:
            total += inner.surface_area
        return total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "solid",
            "id": self.id,
            "outer_shell": self.outer_shell.to_dict(),
            "inner_shells": [s.to_dict() for s in self.inner_shells],
            "surface_area": self.surface_area
        }


def calculate_edge_parameters(
    edge_type: EdgeType,
    start_point: Point2D,
    end_point: Point2D,
    **kwargs
) -> Dict[str, Any]:
    """
    Calculate mathematically sound parameters for edge geometry.

    Args:
        edge_type: Type of edge curve
        start_point: Edge start point
        end_point: Edge end point
        **kwargs: Additional parameters depending on edge type

    Returns:
        Dictionary of curve parameters

    For LINE:
        - No additional parameters needed

    For ARC:
        - center: Optional[Point2D] - if not provided, calculated from bulge or midpoint
        - radius: Optional[float] - calculated from center if not provided
        - bulge: Optional[float] - alternative arc specification
        - midpoint: Optional[Point2D] - point on arc for 3-point arc definition

    For BEZIER:
        - control_points: Optional[List[Point2D]] - interior control points
        - tangent_start: Optional[Vector2D] - start tangent direction
        - tangent_end: Optional[Vector2D] - end tangent direction

    For BSPLINE:
        - control_points: List[Point2D] - all control points including endpoints
        - degree: int - spline degree (default 3)
        - knots: Optional[List[float]] - knot vector

    For NURBS:
        - control_points: List[Point2D]
        - weights: List[float]
        - degree: int
        - knots: Optional[List[float]]
    """
    params: Dict[str, Any] = {}

    if edge_type == EdgeType.LINE:
        # No special parameters for lines
        pass

    elif edge_type == EdgeType.ARC:
        # Calculate arc parameters
        center = kwargs.get("center")
        radius = kwargs.get("radius")
        bulge = kwargs.get("bulge")
        midpoint = kwargs.get("midpoint")

        if bulge is not None:
            # Calculate from bulge (DXF convention)
            # bulge = tan(angle/4)
            # Positive bulge = CCW arc, negative = CW arc
            chord = Vector2D(end_point.x - start_point.x, end_point.y - start_point.y)
            chord_length = chord.magnitude

            # Sagitta (height of arc from chord midpoint)
            sagitta = abs(bulge) * chord_length / 2

            # Radius from chord and sagitta
            radius = (chord_length**2 / 4 + sagitta**2) / (2 * sagitta)

            # Center perpendicular to chord at midpoint
            chord_mid = Point2D(
                (start_point.x + end_point.x) / 2,
                (start_point.y + end_point.y) / 2
            )

            # Perpendicular direction
            perp = chord.perpendicular().normalize()
            if bulge < 0:
                perp = Vector2D(-perp.x, -perp.y)

            # Distance from chord midpoint to center
            h = radius - sagitta

            center = Point2D(
                chord_mid.x + perp.x * h,
                chord_mid.y + perp.y * h
            )

        elif midpoint is not None:
            # Three-point arc: calculate circumcircle
            # Using the circumcenter formula
            ax, ay = start_point.x, start_point.y
            bx, by = midpoint.x, midpoint.y
            cx, cy = end_point.x, end_point.y

            d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
            if abs(d) < 1e-10:
                # Collinear points - use line
                return {"error": "Points are collinear, cannot form arc"}

            ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) +
                  (cx**2 + cy**2) * (ay - by)) / d
            uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) +
                  (cx**2 + cy**2) * (bx - ax)) / d

            center = Point2D(ux, uy)
            radius = center.distance_to(start_point)

        elif center is None:
            # Default: semicircle between points
            chord_mid = Point2D(
                (start_point.x + end_point.x) / 2,
                (start_point.y + end_point.y) / 2
            )
            chord = Vector2D(end_point.x - start_point.x, end_point.y - start_point.y)
            radius = chord.magnitude / 2
            center = chord_mid

        if radius is None and center is not None:
            radius = center.distance_to(start_point)

        # Calculate start and end angles
        start_angle = math.atan2(start_point.y - center.y, start_point.x - center.x)
        end_angle = math.atan2(end_point.y - center.y, end_point.x - center.x)

        params = {
            "center": center,
            "radius": radius,
            "start_angle": start_angle,
            "end_angle": end_angle
        }

    elif edge_type == EdgeType.BEZIER:
        control_points = kwargs.get("control_points", [])
        tangent_start = kwargs.get("tangent_start")
        tangent_end = kwargs.get("tangent_end")

        if not control_points and tangent_start and tangent_end:
            # Create cubic Bezier from tangents
            chord_length = start_point.distance_to(end_point)
            scale = chord_length / 3.0

            # Handle both dict and object tangent formats
            if isinstance(tangent_start, dict):
                ts_x, ts_y = tangent_start.get('x', 0), tangent_start.get('y', 0)
            else:
                ts_x, ts_y = tangent_start.x, tangent_start.y

            if isinstance(tangent_end, dict):
                te_x, te_y = tangent_end.get('x', 0), tangent_end.get('y', 0)
            else:
                te_x, te_y = tangent_end.x, tangent_end.y

            cp1 = Point2D(
                start_point.x + ts_x * scale,
                start_point.y + ts_y * scale
            )
            cp2 = Point2D(
                end_point.x - te_x * scale,
                end_point.y - te_y * scale
            )
            control_points = [start_point, cp1, cp2, end_point]

        elif not control_points:
            # Default: linear (degenerate Bezier)
            control_points = [start_point, end_point]

        params = {"control_points": control_points}

    elif edge_type == EdgeType.BSPLINE:
        control_points = kwargs.get("control_points", [start_point, end_point])
        degree = kwargs.get("degree", 3)
        knots = kwargs.get("knots")

        # Ensure degree is valid
        n = len(control_points) - 1
        degree = min(degree, n)

        params = {
            "control_points": control_points,
            "degree": degree,
            "knots": knots
        }

    elif edge_type == EdgeType.NURBS:
        control_points = kwargs.get("control_points", [start_point, end_point])
        weights = kwargs.get("weights", [1.0] * len(control_points))
        degree = kwargs.get("degree", 3)
        knots = kwargs.get("knots")

        # Ensure valid configuration
        n = len(control_points) - 1
        degree = min(degree, n)

        if len(weights) != len(control_points):
            weights = [1.0] * len(control_points)

        params = {
            "control_points": control_points,
            "weights": weights,
            "degree": degree,
            "knots": knots
        }

    return params


def calculate_surface_parameters(
    surface_type: SurfaceType,
    **kwargs
) -> Dict[str, Any]:
    """
    Calculate mathematically sound parameters for surface geometry.

    Args:
        surface_type: Type of surface
        **kwargs: Additional parameters depending on surface type

    Returns:
        Dictionary of surface parameters

    For PLANE:
        - point: Point3D - point on plane
        - normal: Vector3D - plane normal
        OR
        - three points: p1, p2, p3 - three non-collinear points

    For CYLINDER:
        - axis_point: Point3D - point on axis
        - axis_direction: Vector3D - axis direction
        - radius: float

    For CONE:
        - apex: Point3D - cone apex
        - axis_direction: Vector3D
        - half_angle: float - cone half-angle in radians

    For SPHERE:
        - center: Point3D
        - radius: float

    For TORUS:
        - center: Point3D
        - axis: Vector3D
        - major_radius: float
        - minor_radius: float
    """
    params: Dict[str, Any] = {}

    if surface_type == SurfaceType.PLANE:
        point = kwargs.get("point")
        normal = kwargs.get("normal")
        p1 = kwargs.get("p1")
        p2 = kwargs.get("p2")
        p3 = kwargs.get("p3")

        if p1 and p2 and p3:
            # Calculate plane from three points
            v1 = p2 - p1
            v2 = p3 - p1
            normal = v1.cross(v2).normalize()
            point = p1

        params = {
            "point": point or Point3D(0, 0, 0),
            "normal": normal or Vector3D(0, 0, 1)
        }

    elif surface_type == SurfaceType.CYLINDER:
        axis_point = kwargs.get("axis_point", Point3D(0, 0, 0))
        axis_direction = kwargs.get("axis_direction", Vector3D(0, 0, 1))
        radius = kwargs.get("radius", 1.0)

        params = {
            "axis_point": axis_point,
            "axis_direction": axis_direction.normalize(),
            "radius": radius
        }

    elif surface_type == SurfaceType.CONE:
        apex = kwargs.get("apex", Point3D(0, 0, 0))
        axis_direction = kwargs.get("axis_direction", Vector3D(0, 0, 1))
        half_angle = kwargs.get("half_angle", math.pi / 6)  # 30 degrees default

        params = {
            "apex": apex,
            "axis_direction": axis_direction.normalize(),
            "half_angle": half_angle
        }

    elif surface_type == SurfaceType.SPHERE:
        center = kwargs.get("center", Point3D(0, 0, 0))
        radius = kwargs.get("radius", 1.0)

        params = {
            "center": center,
            "radius": radius
        }

    elif surface_type == SurfaceType.TORUS:
        center = kwargs.get("center", Point3D(0, 0, 0))
        axis = kwargs.get("axis", Vector3D(0, 0, 1))
        major_radius = kwargs.get("major_radius", 2.0)
        minor_radius = kwargs.get("minor_radius", 0.5)

        params = {
            "center": center,
            "axis": axis.normalize(),
            "major_radius": major_radius,
            "minor_radius": minor_radius
        }

    return params


def create_edge_from_points(
    points: List[Point2D],
    edge_type: EdgeType = EdgeType.LINE,
    **kwargs
) -> BRepEdge:
    """
    Convenience function to create a BRep edge from a list of points.

    For LINE: uses first and last points
    For ARC: uses first, last, and optionally middle point
    For BEZIER/BSPLINE/NURBS: uses all points as control points
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points to create an edge")

    start = BRepVertex(Point3D.from_2d(points[0]))
    end = BRepVertex(Point3D.from_2d(points[-1]))

    if edge_type == EdgeType.LINE:
        params = {}

    elif edge_type == EdgeType.ARC and len(points) >= 3:
        # Use middle point for arc definition
        mid_idx = len(points) // 2
        params = calculate_edge_parameters(
            edge_type, points[0], points[-1],
            midpoint=points[mid_idx]
        )

    elif edge_type in (EdgeType.BEZIER, EdgeType.BSPLINE, EdgeType.NURBS):
        params = calculate_edge_parameters(
            edge_type, points[0], points[-1],
            control_points=points,
            **kwargs
        )
    else:
        params = calculate_edge_parameters(
            edge_type, points[0], points[-1], **kwargs
        )

    return BRepEdge(start, end, edge_type, params)


def polygon_to_loop(polygon: Polygon) -> BRepLoop:
    """Convert a Polygon to a BRep loop with line edges."""
    vertices = polygon.vertices
    edges = []

    for i in range(len(vertices)):
        j = (i + 1) % len(vertices) if polygon.closed else i + 1
        if j >= len(vertices):
            break

        start = BRepVertex(Point3D.from_2d(vertices[i]))
        end = BRepVertex(Point3D.from_2d(vertices[j]))
        edge = BRepEdge(start, end, EdgeType.LINE)
        edges.append(edge)

    return BRepLoop(edges, is_outer=True)
