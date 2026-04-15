"""
Curve Mathematics Module

Provides mathematically sound implementations for:
- Bezier curves (quadratic, cubic, and general degree)
- B-Spline curves (uniform and non-uniform)
- NURBS curves (Non-Uniform Rational B-Splines)
- Polynomial interpolation
- Arc parameterization

All implementations follow standard CAD/mathematical definitions with
proper handling of knot vectors, weights, and continuity conditions.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Sequence, Union
import numpy as np
from enum import Enum

from .geometry import Point2D, Point3D, Vector2D


class CurveType(Enum):
    """Types of parametric curves."""
    BEZIER = "bezier"
    BSPLINE = "bspline"
    NURBS = "nurbs"
    POLYNOMIAL = "polynomial"


@dataclass
class BezierCurve:
    """
    Bezier curve of arbitrary degree.

    Mathematical Definition:
    B(t) = sum_{i=0}^{n} C(n,i) * (1-t)^(n-i) * t^i * P_i

    where:
    - n is the degree (number of control points - 1)
    - C(n,i) is the binomial coefficient
    - P_i are the control points
    - t is the parameter in [0, 1]

    Properties:
    - Degree n requires n+1 control points
    - Curve passes through first and last control points
    - Tangent at endpoints aligns with first/last edge of control polygon
    - Curve is contained within convex hull of control points
    """
    control_points: List[Point2D]
    _binomial_cache: dict = field(default_factory=dict, repr=False)

    @property
    def degree(self) -> int:
        """Degree of the Bezier curve (n = num_points - 1)."""
        return len(self.control_points) - 1

    @staticmethod
    def binomial(n: int, k: int) -> int:
        """
        Compute binomial coefficient C(n,k) = n! / (k! * (n-k)!)
        """
        if k < 0 or k > n:
            return 0
        if k == 0 or k == n:
            return 1
        # Use symmetry and iterative calculation for efficiency
        k = min(k, n - k)
        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)
        return result

    def bernstein(self, i: int, n: int, t: float) -> float:
        """
        Bernstein basis polynomial B_{i,n}(t).

        B_{i,n}(t) = C(n,i) * t^i * (1-t)^(n-i)
        """
        return self.binomial(n, i) * (t ** i) * ((1 - t) ** (n - i))

    def evaluate(self, t: float) -> Point2D:
        """
        Evaluate curve at parameter t using de Casteljau's algorithm.

        de Casteljau's algorithm is numerically more stable than
        direct Bernstein polynomial evaluation.

        Time complexity: O(n^2) where n is the degree
        """
        if not 0 <= t <= 1:
            raise ValueError(f"Parameter t must be in [0, 1], got {t}")

        points = [p for p in self.control_points]
        n = len(points)

        # de Casteljau's recursive interpolation
        for r in range(1, n):
            for i in range(n - r):
                x = (1 - t) * points[i].x + t * points[i + 1].x
                y = (1 - t) * points[i].y + t * points[i + 1].y
                points[i] = Point2D(x, y)

        return points[0]

    def derivative(self, t: float) -> Vector2D:
        """
        Compute first derivative (tangent vector) at parameter t.

        B'(t) = n * sum_{i=0}^{n-1} B_{i,n-1}(t) * (P_{i+1} - P_i)
        """
        n = self.degree
        if n < 1:
            return Vector2D(0, 0)

        # Compute derivative control points (hodograph)
        deriv_points = []
        for i in range(n):
            dx = n * (self.control_points[i + 1].x - self.control_points[i].x)
            dy = n * (self.control_points[i + 1].y - self.control_points[i].y)
            deriv_points.append(Point2D(dx, dy))

        # Evaluate derivative curve at t
        deriv_curve = BezierCurve(deriv_points)
        result = deriv_curve.evaluate(t)
        return Vector2D(result.x, result.y)

    def curvature(self, t: float) -> float:
        """
        Compute curvature kappa at parameter t.

        kappa = |x'*y'' - y'*x''| / (x'^2 + y'^2)^(3/2)
        """
        n = self.degree
        if n < 2:
            return 0.0

        # First derivative
        d1 = self.derivative(t)

        # Second derivative via hodograph
        deriv_points = []
        for i in range(n):
            dx = n * (self.control_points[i + 1].x - self.control_points[i].x)
            dy = n * (self.control_points[i + 1].y - self.control_points[i].y)
            deriv_points.append(Point2D(dx, dy))

        deriv_curve = BezierCurve(deriv_points)
        d2_point = deriv_curve.derivative(t) if n > 1 else Vector2D(0, 0)

        # Curvature formula
        cross = d1.x * d2_point.y - d1.y * d2_point.x
        denom = (d1.x**2 + d1.y**2) ** 1.5

        if abs(denom) < 1e-10:
            return 0.0

        return abs(cross) / denom

    def split(self, t: float) -> Tuple[BezierCurve, BezierCurve]:
        """
        Split curve at parameter t into two Bezier curves.

        Uses de Casteljau's algorithm to compute the split.
        """
        left_points = []
        right_points = []

        points = [p for p in self.control_points]
        n = len(points)

        left_points.append(points[0])
        right_points.append(points[-1])

        for r in range(1, n):
            for i in range(n - r):
                x = (1 - t) * points[i].x + t * points[i + 1].x
                y = (1 - t) * points[i].y + t * points[i + 1].y
                points[i] = Point2D(x, y)

            left_points.append(points[0])
            right_points.append(points[n - r - 1])

        right_points.reverse()
        return BezierCurve(left_points), BezierCurve(right_points)

    def sample(self, num_points: int = 50) -> List[Point2D]:
        """Sample the curve at uniform parameter intervals."""
        return [self.evaluate(t / (num_points - 1)) for t in range(num_points)]

    def arc_length(self, num_samples: int = 100) -> float:
        """
        Approximate arc length by sampling.

        For exact arc length, numerical integration would be needed,
        but sampling is sufficient for most CAD applications.
        """
        points = self.sample(num_samples)
        length = 0.0
        for i in range(len(points) - 1):
            length += points[i].distance_to(points[i + 1])
        return length

    @classmethod
    def from_points_and_tangents(cls, p0: Point2D, p1: Point2D,
                                  t0: Vector2D, t1: Vector2D) -> BezierCurve:
        """
        Create cubic Bezier from endpoints and tangent vectors.

        This is useful for creating smooth curves that pass through
        two points with specified directions.
        """
        # Scale tangents to 1/3 of chord length for reasonable curvature
        chord_length = p0.distance_to(p1)
        scale = chord_length / 3.0

        cp1 = Point2D(p0.x + t0.x * scale, p0.y + t0.y * scale)
        cp2 = Point2D(p1.x - t1.x * scale, p1.y - t1.y * scale)

        return cls([p0, cp1, cp2, p1])

    @classmethod
    def quadratic(cls, p0: Point2D, p1: Point2D, p2: Point2D) -> BezierCurve:
        """Create a quadratic (degree 2) Bezier curve."""
        return cls([p0, p1, p2])

    @classmethod
    def cubic(cls, p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D) -> BezierCurve:
        """Create a cubic (degree 3) Bezier curve."""
        return cls([p0, p1, p2, p3])


@dataclass
class BSplineCurve:
    """
    B-Spline curve.

    Mathematical Definition:
    C(u) = sum_{i=0}^{n} N_{i,p}(u) * P_i

    where:
    - N_{i,p}(u) are the B-spline basis functions of degree p
    - P_i are the control points
    - u is the parameter

    Knot Vector Types:
    - Uniform: evenly spaced knots
    - Open (Clamped): curve passes through endpoints
    - Non-uniform: arbitrary knot spacing

    Properties:
    - Local control: moving one control point only affects nearby curve
    - C^(p-k) continuity at knot with multiplicity k
    - Degree p curve needs at least p+1 control points
    """
    control_points: List[Point2D]
    degree: int = 3
    knots: Optional[List[float]] = None
    _basis_cache: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Initialize knot vector if not provided."""
        n = len(self.control_points) - 1
        p = self.degree

        if n < p:
            raise ValueError(
                f"Need at least {p + 1} control points for degree {p} B-spline, "
                f"got {len(self.control_points)}"
            )

        if self.knots is None:
            # Create clamped uniform knot vector
            self.knots = self._create_clamped_knots(n, p)
        else:
            # Validate provided knot vector
            expected_knots = n + p + 2
            if len(self.knots) != expected_knots:
                raise ValueError(
                    f"Knot vector should have {expected_knots} knots, "
                    f"got {len(self.knots)}"
                )

    def _create_clamped_knots(self, n: int, p: int) -> List[float]:
        """
        Create clamped (open) uniform knot vector.

        For n+1 control points and degree p:
        - First p+1 knots are 0
        - Last p+1 knots are 1
        - Middle knots are uniformly spaced
        """
        m = n + p + 1  # Total knots - 1
        knots = []

        # First p+1 knots = 0
        knots.extend([0.0] * (p + 1))

        # Internal knots
        num_internal = m - 2 * p
        for i in range(1, num_internal):
            knots.append(i / num_internal)

        # Last p+1 knots = 1
        knots.extend([1.0] * (p + 1))

        return knots

    def basis_function(self, i: int, p: int, u: float) -> float:
        """
        Compute B-spline basis function N_{i,p}(u) using Cox-de Boor recursion.

        N_{i,0}(u) = 1 if u_i <= u < u_{i+1}, else 0
        N_{i,p}(u) = (u - u_i)/(u_{i+p} - u_i) * N_{i,p-1}(u)
                   + (u_{i+p+1} - u)/(u_{i+p+1} - u_{i+1}) * N_{i+1,p-1}(u)

        Special handling for 0/0 = 0 convention.
        """
        knots = self.knots

        # Base case: degree 0
        if p == 0:
            if knots[i] <= u < knots[i + 1]:
                return 1.0
            # Handle endpoint
            if u == knots[-1] and knots[i] <= u <= knots[i + 1]:
                return 1.0
            return 0.0

        # Recursive case
        denom1 = knots[i + p] - knots[i]
        denom2 = knots[i + p + 1] - knots[i + 1]

        term1 = 0.0
        term2 = 0.0

        if abs(denom1) > 1e-10:
            term1 = (u - knots[i]) / denom1 * self.basis_function(i, p - 1, u)

        if abs(denom2) > 1e-10:
            term2 = (knots[i + p + 1] - u) / denom2 * self.basis_function(i + 1, p - 1, u)

        return term1 + term2

    def evaluate(self, u: float) -> Point2D:
        """
        Evaluate B-spline curve at parameter u.

        C(u) = sum_{i=0}^{n} N_{i,p}(u) * P_i
        """
        # Clamp u to valid range
        u = max(self.knots[0], min(self.knots[-1], u))

        n = len(self.control_points) - 1
        p = self.degree

        x = y = 0.0
        for i in range(n + 1):
            basis = self.basis_function(i, p, u)
            x += basis * self.control_points[i].x
            y += basis * self.control_points[i].y

        return Point2D(x, y)

    def derivative(self, u: float, order: int = 1) -> Vector2D:
        """
        Compute derivative of specified order at parameter u.

        Uses the derivative formula for B-splines.
        """
        if order == 0:
            p = self.evaluate(u)
            return Vector2D(p.x, p.y)

        if order > self.degree:
            return Vector2D(0, 0)

        # Compute derivative control points
        p = self.degree
        n = len(self.control_points) - 1

        # Derivative control points
        deriv_points = []
        for i in range(n):
            denom = self.knots[i + p + 1] - self.knots[i + 1]
            if abs(denom) < 1e-10:
                deriv_points.append(Point2D(0, 0))
            else:
                scale = p / denom
                dx = scale * (self.control_points[i + 1].x - self.control_points[i].x)
                dy = scale * (self.control_points[i + 1].y - self.control_points[i].y)
                deriv_points.append(Point2D(dx, dy))

        # Create derivative B-spline
        deriv_knots = self.knots[1:-1]  # Remove first and last knot
        deriv_spline = BSplineCurve(deriv_points, p - 1, deriv_knots)

        if order == 1:
            result = deriv_spline.evaluate(u)
            return Vector2D(result.x, result.y)
        else:
            return deriv_spline.derivative(u, order - 1)

    def sample(self, num_points: int = 50) -> List[Point2D]:
        """Sample the curve at uniform parameter intervals."""
        u_min = self.knots[self.degree]
        u_max = self.knots[-self.degree - 1]
        points = []
        for i in range(num_points):
            u = u_min + (u_max - u_min) * i / (num_points - 1)
            points.append(self.evaluate(u))
        return points

    def insert_knot(self, u: float) -> BSplineCurve:
        """
        Insert a knot at parameter u using Boehm's algorithm.

        Returns a new B-spline with the same shape but one additional knot.
        """
        p = self.degree
        knots = self.knots.copy()
        points = [Point2D(cp.x, cp.y) for cp in self.control_points]

        # Find knot span
        k = 0
        for i in range(len(knots) - 1):
            if knots[i] <= u < knots[i + 1]:
                k = i
                break

        # Compute new control points
        new_points = []
        for i in range(len(points) + 1):
            if i <= k - p:
                new_points.append(points[i])
            elif i >= k + 1:
                new_points.append(points[i - 1])
            else:
                alpha = (u - knots[i]) / (knots[i + p] - knots[i])
                x = (1 - alpha) * points[i - 1].x + alpha * points[i].x
                y = (1 - alpha) * points[i - 1].y + alpha * points[i].y
                new_points.append(Point2D(x, y))

        # Insert knot into knot vector
        new_knots = knots[:k + 1] + [u] + knots[k + 1:]

        return BSplineCurve(new_points, p, new_knots)

    @classmethod
    def interpolate(cls, points: List[Point2D], degree: int = 3) -> BSplineCurve:
        """
        Create a B-spline that interpolates through the given points.

        Uses global B-spline interpolation with chord-length parameterization.
        """
        n = len(points) - 1
        p = min(degree, n)

        # Chord-length parameterization
        total_length = 0.0
        chord_lengths = [0.0]
        for i in range(n):
            dist = points[i].distance_to(points[i + 1])
            total_length += dist
            chord_lengths.append(total_length)

        # Normalize to [0, 1]
        params = [c / total_length if total_length > 0 else i / n
                  for i, c in enumerate(chord_lengths)]

        # Create knot vector (averaging method)
        knots = [0.0] * (p + 1)
        for j in range(1, n - p + 1):
            knot_sum = sum(params[j:j + p]) / p
            knots.append(knot_sum)
        knots.extend([1.0] * (p + 1))

        # Build coefficient matrix and solve for control points
        A = np.zeros((n + 1, n + 1))
        for i in range(n + 1):
            temp_spline = BSplineCurve([Point2D(0, 0)] * (n + 1), p, knots)
            for j in range(n + 1):
                A[i, j] = temp_spline.basis_function(j, p, params[i])

        # Solve for control point coordinates
        px = np.array([pt.x for pt in points])
        py = np.array([pt.y for pt in points])

        try:
            cx = np.linalg.solve(A, px)
            cy = np.linalg.solve(A, py)
        except np.linalg.LinAlgError:
            # Fallback: use points directly as control points
            return cls(points, p)

        control_points = [Point2D(cx[i], cy[i]) for i in range(n + 1)]
        return cls(control_points, p, knots)


@dataclass
class NURBSCurve:
    """
    Non-Uniform Rational B-Spline (NURBS) curve.

    Mathematical Definition:
    C(u) = sum_{i=0}^{n} R_{i,p}(u) * P_i

    where R_{i,p}(u) are the rational basis functions:
    R_{i,p}(u) = N_{i,p}(u) * w_i / sum_{j=0}^{n} N_{j,p}(u) * w_j

    Properties:
    - All B-spline properties plus:
    - Weights provide additional control over curve shape
    - Can exactly represent conic sections (circles, ellipses, etc.)
    - Projective invariance
    """
    control_points: List[Point2D]
    weights: List[float]
    degree: int = 3
    knots: Optional[List[float]] = None
    _bspline: BSplineCurve = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize internal B-spline and validate weights."""
        n = len(self.control_points)
        if len(self.weights) != n:
            raise ValueError(
                f"Number of weights ({len(self.weights)}) must match "
                f"number of control points ({n})"
            )

        if any(w <= 0 for w in self.weights):
            raise ValueError("All weights must be positive")

        # Create weighted control points in homogeneous coordinates
        weighted_points = [
            Point2D(p.x * w, p.y * w)
            for p, w in zip(self.control_points, self.weights)
        ]

        self._bspline = BSplineCurve(weighted_points, self.degree, self.knots)
        if self.knots is None:
            self.knots = self._bspline.knots

    def evaluate(self, u: float) -> Point2D:
        """
        Evaluate NURBS curve at parameter u.

        Uses the ratio of weighted B-spline evaluations.
        """
        # Evaluate weighted point
        weighted_pt = self._bspline.evaluate(u)

        # Compute weight sum
        n = len(self.control_points) - 1
        p = self.degree
        weight_sum = 0.0
        for i in range(n + 1):
            basis = self._bspline.basis_function(i, p, u)
            weight_sum += basis * self.weights[i]

        if abs(weight_sum) < 1e-10:
            return Point2D(0, 0)

        return Point2D(weighted_pt.x / weight_sum, weighted_pt.y / weight_sum)

    def derivative(self, u: float) -> Vector2D:
        """
        Compute first derivative at parameter u.

        Uses the quotient rule for rational functions.
        """
        # Get weighted B-spline derivatives
        A = self._bspline.evaluate(u)
        A_deriv = self._bspline.derivative(u)

        # Compute weight function and its derivative
        n = len(self.control_points) - 1
        p = self.degree
        w = 0.0
        w_deriv = 0.0

        for i in range(n + 1):
            basis = self._bspline.basis_function(i, p, u)
            w += basis * self.weights[i]

        # Weight derivative from weighted B-spline
        weight_points = [Point2D(w, 0) for w in self.weights]
        weight_spline = BSplineCurve(weight_points, p, self.knots)
        w_deriv_pt = weight_spline.derivative(u)
        w_deriv = w_deriv_pt.x

        if abs(w) < 1e-10:
            return Vector2D(0, 0)

        # Quotient rule: (A/w)' = (A'*w - A*w') / w^2
        dx = (A_deriv.x * w - A.x * w_deriv) / (w * w)
        dy = (A_deriv.y * w - A.y * w_deriv) / (w * w)

        return Vector2D(dx, dy)

    def sample(self, num_points: int = 50) -> List[Point2D]:
        """Sample the curve at uniform parameter intervals."""
        u_min = self.knots[self.degree]
        u_max = self.knots[-self.degree - 1]
        points = []
        for i in range(num_points):
            u = u_min + (u_max - u_min) * i / (num_points - 1)
            points.append(self.evaluate(u))
        return points

    @classmethod
    def circle(cls, center: Point2D, radius: float,
               start_angle: float = 0, end_angle: float = 2 * math.pi) -> NURBSCurve:
        """
        Create a NURBS representation of a circular arc.

        Uses the standard 9-point representation for a full circle,
        or fewer points for arcs.
        """
        # For a full circle, use 9 control points (quadratic NURBS)
        if abs(end_angle - start_angle - 2 * math.pi) < 1e-10:
            # Full circle
            w = math.sqrt(2) / 2  # Weight for corner control points

            angles = [0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi,
                      5 * math.pi / 4, 3 * math.pi / 2, 7 * math.pi / 4, 2 * math.pi]
            weights = [1, w, 1, w, 1, w, 1, w, 1]

            control_points = []
            for i, angle in enumerate(angles):
                if weights[i] == 1:
                    x = center.x + radius * math.cos(angle + start_angle)
                    y = center.y + radius * math.sin(angle + start_angle)
                else:
                    # Corner points are at radius/cos(45°)
                    x = center.x + radius / w * math.cos(angle + start_angle)
                    y = center.y + radius / w * math.sin(angle + start_angle)
                control_points.append(Point2D(x, y))

            knots = [0, 0, 0, 0.25, 0.25, 0.5, 0.5, 0.75, 0.75, 1, 1, 1]
            return cls(control_points, weights, degree=2, knots=knots)

        # For arcs, create appropriate representation
        arc_angle = end_angle - start_angle
        num_segments = max(1, int(abs(arc_angle) / (math.pi / 2) + 0.5))

        control_points = []
        weights = []

        for seg in range(num_segments):
            seg_start = start_angle + arc_angle * seg / num_segments
            seg_end = start_angle + arc_angle * (seg + 1) / num_segments
            half_angle = (seg_end - seg_start) / 2

            # Start point
            x0 = center.x + radius * math.cos(seg_start)
            y0 = center.y + radius * math.sin(seg_start)

            # End point
            x2 = center.x + radius * math.cos(seg_end)
            y2 = center.y + radius * math.sin(seg_end)

            # Middle control point (weighted)
            mid_angle = (seg_start + seg_end) / 2
            w = math.cos(half_angle)
            x1 = center.x + radius / w * math.cos(mid_angle)
            y1 = center.y + radius / w * math.sin(mid_angle)

            if seg == 0:
                control_points.append(Point2D(x0, y0))
                weights.append(1.0)

            control_points.append(Point2D(x1, y1))
            weights.append(w)

            control_points.append(Point2D(x2, y2))
            weights.append(1.0)

        # Create knot vector
        n = len(control_points) - 1
        knots = [0, 0, 0]
        for i in range(1, num_segments):
            knots.extend([i / num_segments, i / num_segments])
        knots.extend([1, 1, 1])

        return cls(control_points, weights, degree=2, knots=knots)


@dataclass
class PolynomialInterpolator:
    """
    Polynomial curve interpolation.

    Supports various interpolation methods:
    - Lagrange interpolation
    - Newton's divided differences
    - Hermite interpolation (with derivatives)
    """
    points: List[Point2D]
    method: str = "lagrange"
    derivatives: Optional[List[Vector2D]] = None

    def _lagrange_basis(self, i: int, t: float, params: List[float]) -> float:
        """
        Compute Lagrange basis polynomial L_i(t).

        L_i(t) = product_{j!=i} (t - t_j) / (t_i - t_j)
        """
        n = len(params)
        result = 1.0
        for j in range(n):
            if j != i:
                denom = params[i] - params[j]
                if abs(denom) < 1e-10:
                    continue
                result *= (t - params[j]) / denom
        return result

    def evaluate(self, t: float) -> Point2D:
        """
        Evaluate interpolating polynomial at parameter t.
        """
        n = len(self.points)
        if n == 0:
            return Point2D(0, 0)

        # Create parameterization (chord-length)
        params = [0.0]
        total_length = 0.0
        for i in range(n - 1):
            total_length += self.points[i].distance_to(self.points[i + 1])
            params.append(total_length)

        if total_length > 0:
            params = [p / total_length for p in params]

        if self.method == "lagrange":
            x = y = 0.0
            for i in range(n):
                L_i = self._lagrange_basis(i, t, params)
                x += L_i * self.points[i].x
                y += L_i * self.points[i].y
            return Point2D(x, y)

        elif self.method == "hermite" and self.derivatives:
            # Hermite cubic interpolation between pairs of points
            # Find segment
            seg = 0
            for i in range(n - 1):
                if params[i] <= t <= params[i + 1]:
                    seg = i
                    break

            # Local parameter
            t0, t1 = params[seg], params[seg + 1]
            if abs(t1 - t0) < 1e-10:
                return self.points[seg]

            s = (t - t0) / (t1 - t0)

            # Hermite basis functions
            h00 = 2 * s**3 - 3 * s**2 + 1
            h10 = s**3 - 2 * s**2 + s
            h01 = -2 * s**3 + 3 * s**2
            h11 = s**3 - s**2

            # Interval length for scaling tangents
            dt = t1 - t0

            p0 = self.points[seg]
            p1 = self.points[seg + 1]
            m0 = self.derivatives[seg] if seg < len(self.derivatives) else Vector2D(0, 0)
            m1 = self.derivatives[seg + 1] if seg + 1 < len(self.derivatives) else Vector2D(0, 0)

            x = h00 * p0.x + h10 * dt * m0.x + h01 * p1.x + h11 * dt * m1.x
            y = h00 * p0.y + h10 * dt * m0.y + h01 * p1.y + h11 * dt * m1.y

            return Point2D(x, y)

        return self.points[0]

    def sample(self, num_points: int = 50) -> List[Point2D]:
        """Sample the interpolating curve."""
        return [self.evaluate(t / (num_points - 1)) for t in range(num_points)]


@dataclass
class ArcParameterization:
    """
    Arc-length parameterization for curves.

    Converts parameter-based curves to arc-length parameterization
    for uniform sampling along the curve.
    """
    curve: Union[BezierCurve, BSplineCurve, NURBSCurve]
    num_samples: int = 100
    _arc_lengths: List[float] = field(default_factory=list, repr=False)
    _params: List[float] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Build arc-length lookup table."""
        self._build_table()

    def _build_table(self):
        """Build arc-length to parameter mapping."""
        self._arc_lengths = [0.0]
        self._params = [0.0]

        # Get parameter range
        if isinstance(self.curve, BezierCurve):
            u_min, u_max = 0.0, 1.0
        else:
            u_min = self.curve.knots[self.curve.degree]
            u_max = self.curve.knots[-self.curve.degree - 1]

        prev_point = self.curve.evaluate(u_min)
        total_length = 0.0

        for i in range(1, self.num_samples + 1):
            u = u_min + (u_max - u_min) * i / self.num_samples
            point = self.curve.evaluate(u)
            total_length += prev_point.distance_to(point)
            self._arc_lengths.append(total_length)
            self._params.append(u)
            prev_point = point

    @property
    def total_length(self) -> float:
        """Total arc length of the curve."""
        return self._arc_lengths[-1] if self._arc_lengths else 0.0

    def param_at_length(self, s: float) -> float:
        """
        Find parameter u corresponding to arc length s.

        Uses linear interpolation in the lookup table.
        """
        if s <= 0:
            return self._params[0]
        if s >= self.total_length:
            return self._params[-1]

        # Binary search for interval
        lo, hi = 0, len(self._arc_lengths) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self._arc_lengths[mid] < s:
                lo = mid
            else:
                hi = mid

        # Linear interpolation
        s0, s1 = self._arc_lengths[lo], self._arc_lengths[hi]
        u0, u1 = self._params[lo], self._params[hi]

        if abs(s1 - s0) < 1e-10:
            return u0

        t = (s - s0) / (s1 - s0)
        return u0 + t * (u1 - u0)

    def evaluate_at_length(self, s: float) -> Point2D:
        """Evaluate curve at arc length s."""
        u = self.param_at_length(s)
        return self.curve.evaluate(u)

    def sample_uniform(self, num_points: int) -> List[Point2D]:
        """Sample curve at uniform arc-length intervals."""
        points = []
        for i in range(num_points):
            s = self.total_length * i / (num_points - 1)
            points.append(self.evaluate_at_length(s))
        return points
