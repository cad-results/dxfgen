"""
Extended Entity Models with Curve Support

Provides Pydantic models for nonlinear curve entities:
- Spline (B-Spline curves)
- NURBS (Rational B-Spline curves)
- Bezier (Bezier curves)
- Ellipse (Full ellipse or elliptical arc)

These extend the basic entity types (Line, Circle, Arc, Polyline, Hatch)
to support advanced CAD curve representations.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
import math


class Point(BaseModel):
    """2D Point with x and y coordinates."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")


class ControlPoint(BaseModel):
    """Control point with optional weight for NURBS."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    weight: float = Field(default=1.0, description="Weight for rational curves (NURBS)")


class Spline(BaseModel):
    """
    B-Spline curve entity.

    A B-Spline is defined by:
    - Control points: Define the shape of the curve
    - Degree: Polynomial degree (typically 2-5, default 3 for cubic)
    - Knots: Optional knot vector (auto-generated if not provided)

    The curve follows the control polygon but typically doesn't pass
    through interior control points. Use fit_points for interpolation.
    """
    type: str = Field(default="S", description="Entity type (S for Spline)")
    description: str = Field(default="", description="Description of the spline")
    control_points: List[Point] = Field(description="Control points defining the curve shape")
    degree: int = Field(default=3, ge=1, le=10, description="Spline degree (1=linear, 2=quadratic, 3=cubic)")
    knots: Optional[List[float]] = Field(default=None, description="Knot vector (auto-generated if not provided)")
    fit_points: Optional[List[Point]] = Field(default=None, description="Points the curve should pass through")
    closed: bool = Field(default=False, description="Whether the spline is closed")
    layer: str = Field(default="0", description="Layer name")

    @field_validator('control_points')
    @classmethod
    def validate_control_points(cls, v, info):
        degree = info.data.get('degree', 3)
        min_points = degree + 1
        if len(v) < min_points:
            raise ValueError(f"Degree {degree} spline requires at least {min_points} control points")
        return v


class NURBSCurve(BaseModel):
    """
    NURBS (Non-Uniform Rational B-Spline) curve entity.

    NURBS extends B-Splines with:
    - Weights: Each control point has a weight affecting curve attraction
    - Can exactly represent conic sections (circles, ellipses, parabolas)

    Mathematical properties:
    - Weight > 1: Curve pulled toward control point
    - Weight < 1: Curve pushed away from control point
    - Weight = 1: Standard B-Spline behavior
    """
    type: str = Field(default="N", description="Entity type (N for NURBS)")
    description: str = Field(default="", description="Description of the NURBS curve")
    control_points: List[ControlPoint] = Field(description="Weighted control points")
    degree: int = Field(default=3, ge=1, le=10, description="Curve degree")
    knots: Optional[List[float]] = Field(default=None, description="Knot vector")
    closed: bool = Field(default=False, description="Whether the curve is closed")
    layer: str = Field(default="0", description="Layer name")

    @field_validator('control_points')
    @classmethod
    def validate_nurbs_points(cls, v, info):
        degree = info.data.get('degree', 3)
        min_points = degree + 1
        if len(v) < min_points:
            raise ValueError(f"Degree {degree} NURBS requires at least {min_points} control points")
        # Validate weights are positive
        for i, pt in enumerate(v):
            if pt.weight <= 0:
                raise ValueError(f"Weight at index {i} must be positive, got {pt.weight}")
        return v


class BezierCurve(BaseModel):
    """
    Bezier curve entity.

    Bezier curves are polynomial curves defined entirely by control points:
    - 2 points: Linear (degree 1)
    - 3 points: Quadratic (degree 2)
    - 4 points: Cubic (degree 3) - most common
    - n+1 points: Degree n

    Properties:
    - Passes through first and last control points
    - Tangent at endpoints aligns with control polygon
    - Contained within convex hull of control points
    """
    type: str = Field(default="B", description="Entity type (B for Bezier)")
    description: str = Field(default="", description="Description of the Bezier curve")
    control_points: List[Point] = Field(description="Control points (n+1 points for degree n)")
    layer: str = Field(default="0", description="Layer name")

    @property
    def degree(self) -> int:
        """Bezier degree is number of control points minus 1."""
        return len(self.control_points) - 1

    @field_validator('control_points')
    @classmethod
    def validate_bezier_points(cls, v):
        if len(v) < 2:
            raise ValueError("Bezier curve requires at least 2 control points")
        return v


class Ellipse(BaseModel):
    """
    Ellipse or elliptical arc entity.

    Defined by:
    - Center point
    - Major axis endpoint (defines direction and half-length)
    - Ratio: minor/major axis ratio (0 < ratio <= 1)
    - Start/end parameters for arcs (0 to 2*pi for full ellipse)

    Mathematical representation:
    x(t) = center_x + major_x * cos(t) + minor_x * sin(t)
    y(t) = center_y + major_y * cos(t) + minor_y * sin(t)
    where minor = ratio * major rotated 90 degrees
    """
    type: str = Field(default="E", description="Entity type (E for Ellipse)")
    description: str = Field(default="", description="Description of the ellipse")
    center_x: float = Field(description="Center X coordinate")
    center_y: float = Field(description="Center Y coordinate")
    major_axis_x: float = Field(description="Major axis endpoint X (relative to center)")
    major_axis_y: float = Field(description="Major axis endpoint Y (relative to center)")
    ratio: float = Field(ge=0.01, le=1.0, description="Minor/major axis ratio")
    start_param: float = Field(default=0.0, description="Start parameter (radians)")
    end_param: float = Field(default=2*math.pi, description="End parameter (radians)")
    layer: str = Field(default="0", description="Layer name")

    @property
    def major_radius(self) -> float:
        """Length of major axis (semi-major axis)."""
        return math.sqrt(self.major_axis_x**2 + self.major_axis_y**2)

    @property
    def minor_radius(self) -> float:
        """Length of minor axis (semi-minor axis)."""
        return self.major_radius * self.ratio

    @property
    def rotation(self) -> float:
        """Rotation angle of major axis from X-axis (radians)."""
        return math.atan2(self.major_axis_y, self.major_axis_x)

    @property
    def is_full(self) -> bool:
        """Whether this is a full ellipse (not an arc)."""
        return abs(self.end_param - self.start_param - 2*math.pi) < 1e-6


class CurvedVertex(BaseModel):
    """Vertex with optional bulge for curved polylines."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    bulge: float = Field(default=0.0, description="Arc bulge factor (0=straight, 1=semicircle)")
    start_width: float = Field(default=0.0, description="Start width for variable width segment")
    end_width: float = Field(default=0.0, description="End width for variable width segment")


class PolylineWithCurves(BaseModel):
    """
    Extended polyline that can include curved segments.

    Each vertex can have:
    - bulge: Arc bulge factor for curved segments (0 = straight)
    - start_width, end_width: Variable width segments

    Bulge calculation:
    bulge = tan(arc_angle / 4)
    - bulge > 0: Arc curves to the left (CCW)
    - bulge < 0: Arc curves to the right (CW)
    - |bulge| = 1: Semicircle
    """
    type: str = Field(default="PW", description="Entity type (PW for Polyline with curves)")
    description: str = Field(default="", description="Description")
    vertices: List[CurvedVertex] = Field(
        description="Vertices with optional bulge for curved segments"
    )
    closed: bool = Field(default=False, description="Whether the polyline is closed")
    layer: str = Field(default="0", description="Layer name")

    @field_validator('vertices')
    @classmethod
    def validate_vertices(cls, v):
        if len(v) < 2:
            raise ValueError("Polyline requires at least 2 vertices")
        return v


class ExtendedEntities(BaseModel):
    """Collection of all entity types including curves."""

    # Basic entities
    lines: List["Line"] = Field(default_factory=list)
    circles: List["Circle"] = Field(default_factory=list)
    arcs: List["Arc"] = Field(default_factory=list)
    polylines: List["Polyline"] = Field(default_factory=list)
    hatches: List["Hatch"] = Field(default_factory=list)

    # Curve entities
    splines: List[Spline] = Field(default_factory=list, description="B-Spline curves")
    nurbs_curves: List[NURBSCurve] = Field(default_factory=list, description="NURBS curves")
    bezier_curves: List[BezierCurve] = Field(default_factory=list, description="Bezier curves")
    ellipses: List[Ellipse] = Field(default_factory=list, description="Ellipses and elliptical arcs")
    polylines_with_curves: List[PolylineWithCurves] = Field(
        default_factory=list, description="Polylines with curved segments"
    )

    notes: str = Field(default="", description="Additional notes or clarifications")

    def total_entity_count(self) -> int:
        """Total number of entities."""
        return (
            len(self.lines) + len(self.circles) + len(self.arcs) +
            len(self.polylines) + len(self.hatches) +
            len(self.splines) + len(self.nurbs_curves) +
            len(self.bezier_curves) + len(self.ellipses) +
            len(self.polylines_with_curves)
        )

    def has_curves(self) -> bool:
        """Check if any curve entities exist."""
        return (
            len(self.splines) > 0 or
            len(self.nurbs_curves) > 0 or
            len(self.bezier_curves) > 0 or
            len(self.ellipses) > 0 or
            len(self.polylines_with_curves) > 0
        )


# Import basic entity types for type hints
from .entity_extractor import Line, Circle, Arc, Polyline, Hatch

# Update ExtendedEntities to use proper types
ExtendedEntities.model_rebuild()
