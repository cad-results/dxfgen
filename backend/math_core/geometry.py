"""
Core Geometry Module

Provides fundamental geometric primitives and operations with mathematically
sound calculations for both linear and nonlinear geometry.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union, Sequence
import numpy as np


@dataclass
class Point2D:
    """2D Point with x, y coordinates."""
    x: float
    y: float

    def __add__(self, other: Union[Point2D, Vector2D]) -> Point2D:
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Point2D:
        return Point2D(self.x * scalar, self.y * scalar)

    def distance_to(self, other: Point2D) -> float:
        """Euclidean distance to another point."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_numpy(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> Point2D:
        return cls(t[0], t[1])

    @classmethod
    def from_polar(cls, r: float, theta: float) -> Point2D:
        """Create point from polar coordinates (theta in radians)."""
        return cls(r * math.cos(theta), r * math.sin(theta))


@dataclass
class Point3D:
    """3D Point with x, y, z coordinates."""
    x: float
    y: float
    z: float

    def __add__(self, other: Union[Point3D, Vector3D]) -> Point3D:
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Point3D) -> Vector3D:
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Point3D:
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def distance_to(self, other: Point3D) -> float:
        """Euclidean distance to another point."""
        return math.sqrt(
            (self.x - other.x)**2 +
            (self.y - other.y)**2 +
            (self.z - other.z)**2
        )

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_numpy(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def to_2d(self) -> Point2D:
        """Project to 2D (drop z-coordinate)."""
        return Point2D(self.x, self.y)

    @classmethod
    def from_2d(cls, p: Point2D, z: float = 0.0) -> Point3D:
        return cls(p.x, p.y, z)


@dataclass
class Vector2D:
    """2D Vector."""
    x: float
    y: float

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2D:
        return self.__mul__(scalar)

    def __neg__(self) -> Vector2D:
        return Vector2D(-self.x, -self.y)

    @property
    def magnitude(self) -> float:
        """Vector magnitude (length)."""
        return math.sqrt(self.x**2 + self.y**2)

    @property
    def length(self) -> float:
        """Alias for magnitude."""
        return self.magnitude

    def normalize(self) -> Vector2D:
        """Return unit vector in same direction."""
        mag = self.magnitude
        if mag < 1e-10:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)

    def dot(self, other: Vector2D) -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector2D) -> float:
        """2D cross product (scalar result - z-component of 3D cross)."""
        return self.x * other.y - self.y * other.x

    def perpendicular(self) -> Vector2D:
        """Return perpendicular vector (rotated 90 degrees CCW)."""
        return Vector2D(-self.y, self.x)

    def angle(self) -> float:
        """Angle in radians from positive x-axis."""
        return math.atan2(self.y, self.x)

    def rotate(self, theta: float) -> Vector2D:
        """Rotate vector by theta radians."""
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        return Vector2D(
            self.x * cos_t - self.y * sin_t,
            self.x * sin_t + self.y * cos_t
        )

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Vector3D:
    """3D Vector."""
    x: float
    y: float
    z: float

    def __add__(self, other: Vector3D) -> Vector3D:
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3D) -> Vector3D:
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3D:
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vector3D:
        return self.__mul__(scalar)

    def __neg__(self) -> Vector3D:
        return Vector3D(-self.x, -self.y, -self.z)

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> Vector3D:
        mag = self.magnitude
        if mag < 1e-10:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / mag, self.y / mag, self.z / mag)

    def dot(self, other: Vector3D) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3D) -> Vector3D:
        """3D cross product."""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_2d(self) -> Vector2D:
        return Vector2D(self.x, self.y)


@dataclass
class LineSegment:
    """Line segment defined by two endpoints."""
    start: Point2D
    end: Point2D

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def direction(self) -> Vector2D:
        """Unit vector from start to end."""
        return (self.end - self.start).normalize()

    @property
    def midpoint(self) -> Point2D:
        return Point2D(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2
        )

    def point_at(self, t: float) -> Point2D:
        """
        Get point at parameter t (0 <= t <= 1).
        t=0 returns start, t=1 returns end.
        """
        return Point2D(
            self.start.x + t * (self.end.x - self.start.x),
            self.start.y + t * (self.end.y - self.start.y)
        )

    def distance_to_point(self, point: Point2D) -> float:
        """Perpendicular distance from point to line (infinite extension)."""
        # Vector from start to end
        d = self.end - self.start
        # Vector from start to point
        p = point - self.start
        # Project p onto d
        t = p.dot(d) / d.dot(d)
        t = max(0, min(1, t))  # Clamp to segment
        # Closest point on segment
        closest = self.point_at(t)
        return point.distance_to(closest)

    def intersect(self, other: LineSegment) -> Optional[Point2D]:
        """
        Find intersection point with another line segment.
        Returns None if segments don't intersect.
        """
        x1, y1 = self.start.x, self.start.y
        x2, y2 = self.end.x, self.end.y
        x3, y3 = other.start.x, other.start.y
        x4, y4 = other.end.x, other.end.y

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None  # Parallel or coincident

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            return self.point_at(t)
        return None


class Polygon:
    """
    Polygon defined by a list of vertices (in order).
    Can be used for both open polylines and closed polygons.
    """

    def __init__(self, vertices: List[Point2D], closed: bool = True):
        self.vertices = vertices
        self.closed = closed

    @property
    def n_vertices(self) -> int:
        return len(self.vertices)

    @property
    def edges(self) -> List[LineSegment]:
        """Return list of edges as LineSegments."""
        edges = []
        n = len(self.vertices)
        for i in range(n - 1):
            edges.append(LineSegment(self.vertices[i], self.vertices[i + 1]))
        if self.closed and n > 2:
            edges.append(LineSegment(self.vertices[-1], self.vertices[0]))
        return edges

    @property
    def perimeter(self) -> float:
        """Calculate perimeter length."""
        return sum(edge.length for edge in self.edges)

    def to_tuples(self) -> List[Tuple[float, float]]:
        return [v.to_tuple() for v in self.vertices]

    @classmethod
    def from_tuples(cls, points: List[Tuple[float, float]], closed: bool = True) -> Polygon:
        return cls([Point2D.from_tuple(p) for p in points], closed)

    @classmethod
    def regular(cls, n_sides: int, radius: float, center: Point2D = None,
                start_angle: float = 0) -> Polygon:
        """
        Create a regular polygon.

        Args:
            n_sides: Number of sides
            radius: Distance from center to vertices (circumradius)
            center: Center point (default: origin)
            start_angle: Starting angle in radians (default: 0)
        """
        if center is None:
            center = Point2D(0, 0)

        vertices = []
        for i in range(n_sides):
            angle = start_angle + 2 * math.pi * i / n_sides
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            vertices.append(Point2D(x, y))

        return cls(vertices, closed=True)

    @classmethod
    def rectangle(cls, width: float, height: float, center: Point2D = None) -> Polygon:
        """Create a rectangle centered at the given point."""
        if center is None:
            center = Point2D(0, 0)

        hw, hh = width / 2, height / 2
        vertices = [
            Point2D(center.x - hw, center.y - hh),
            Point2D(center.x + hw, center.y - hh),
            Point2D(center.x + hw, center.y + hh),
            Point2D(center.x - hw, center.y + hh),
        ]
        return cls(vertices, closed=True)


def compute_polygon_area(polygon: Polygon) -> float:
    """
    Compute area of a polygon using the Shoelace formula.
    Returns positive area for CCW vertices, negative for CW.

    Mathematical basis:
    A = (1/2) * |sum_{i=0}^{n-1} (x_i * y_{i+1} - x_{i+1} * y_i)|
    """
    if not polygon.closed or len(polygon.vertices) < 3:
        return 0.0

    vertices = polygon.vertices
    n = len(vertices)
    area = 0.0

    for i in range(n):
        j = (i + 1) % n
        area += vertices[i].x * vertices[j].y
        area -= vertices[j].x * vertices[i].y

    return area / 2.0


def compute_centroid(polygon: Polygon) -> Point2D:
    """
    Compute centroid of a polygon.

    Mathematical basis:
    C_x = (1/6A) * sum_{i=0}^{n-1} (x_i + x_{i+1})(x_i*y_{i+1} - x_{i+1}*y_i)
    C_y = (1/6A) * sum_{i=0}^{n-1} (y_i + y_{i+1})(x_i*y_{i+1} - x_{i+1}*y_i)
    """
    if not polygon.closed or len(polygon.vertices) < 3:
        # For open polyline, return average of vertices
        if polygon.vertices:
            cx = sum(v.x for v in polygon.vertices) / len(polygon.vertices)
            cy = sum(v.y for v in polygon.vertices) / len(polygon.vertices)
            return Point2D(cx, cy)
        return Point2D(0, 0)

    area = compute_polygon_area(polygon)
    if abs(area) < 1e-10:
        # Degenerate polygon - return average
        cx = sum(v.x for v in polygon.vertices) / len(polygon.vertices)
        cy = sum(v.y for v in polygon.vertices) / len(polygon.vertices)
        return Point2D(cx, cy)

    vertices = polygon.vertices
    n = len(vertices)
    cx = cy = 0.0

    for i in range(n):
        j = (i + 1) % n
        cross = vertices[i].x * vertices[j].y - vertices[j].x * vertices[i].y
        cx += (vertices[i].x + vertices[j].x) * cross
        cy += (vertices[i].y + vertices[j].y) * cross

    factor = 1.0 / (6.0 * area)
    return Point2D(cx * factor, cy * factor)


def point_in_polygon(point: Point2D, polygon: Polygon) -> bool:
    """
    Test if a point is inside a polygon using ray casting algorithm.

    Mathematical basis:
    Cast a horizontal ray from point to +infinity and count intersections
    with polygon edges. Odd count = inside, even count = outside.
    """
    if not polygon.closed:
        return False

    vertices = polygon.vertices
    n = len(vertices)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = vertices[i].x, vertices[i].y
        xj, yj = vertices[j].x, vertices[j].y

        if ((yi > point.y) != (yj > point.y)) and \
           (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


def offset_polygon(polygon: Polygon, offset: float) -> Polygon:
    """
    Offset a polygon by a given distance.
    Positive offset = outward (enlarge), negative = inward (shrink).

    Mathematical basis:
    For each vertex, compute the bisector direction from adjacent edges
    and move the vertex along the bisector by offset/sin(half_angle).
    """
    if len(polygon.vertices) < 3:
        return polygon

    vertices = polygon.vertices
    n = len(vertices)
    new_vertices = []

    for i in range(n):
        # Get adjacent vertices
        prev_idx = (i - 1) % n
        next_idx = (i + 1) % n

        # Edge vectors (pointing toward current vertex)
        v1 = vertices[i] - vertices[prev_idx]
        v2 = vertices[next_idx] - vertices[i]

        # Normalize
        v1_norm = v1.normalize()
        v2_norm = v2.normalize()

        # Perpendicular vectors (pointing outward for CCW polygon)
        n1 = v1_norm.perpendicular()
        n2 = v2_norm.perpendicular()

        # Bisector direction
        bisector = (n1 + n2).normalize()

        # Calculate offset distance along bisector
        # offset_distance = offset / sin(half_angle)
        # sin(half_angle) = |n1 + n2| / 2
        dot = n1.dot(n2)
        # Clamp to avoid numerical issues at very sharp angles
        dot = max(-0.999, min(0.999, dot))
        sin_half = math.sqrt((1 + dot) / 2)

        if sin_half < 0.01:
            # Very sharp angle - cap the offset
            offset_dist = offset * 10
        else:
            offset_dist = offset / sin_half

        # New vertex position
        new_x = vertices[i].x + bisector.x * offset_dist
        new_y = vertices[i].y + bisector.y * offset_dist
        new_vertices.append(Point2D(new_x, new_y))

    return Polygon(new_vertices, closed=polygon.closed)
