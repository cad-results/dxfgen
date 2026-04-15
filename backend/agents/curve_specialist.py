"""
Curve Specialist Agent - Expert in nonlinear curve generation.

Handles designs requiring:
- B-Spline curves
- NURBS (Non-Uniform Rational B-Splines)
- Bezier curves
- Ellipses and elliptical arcs
- Smooth interpolation through points
- Organic/freeform shapes
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import math

from .curve_entities import (
    Spline, NURBSCurve, BezierCurve, Ellipse,
    PolylineWithCurves, ExtendedEntities, Point, ControlPoint
)
from .entity_extractor import Line, Circle, Arc, Polyline, Hatch


class CurveDesignParameters(BaseModel):
    """Parameters extracted for curve-based designs."""

    curve_type: str = Field(
        description="Primary curve type: 'bezier', 'bspline', 'nurbs', 'ellipse', 'mixed'"
    )
    smoothness_level: str = Field(
        default="high",
        description="Smoothness requirement: 'low' (G0), 'medium' (G1), 'high' (G2/curvature continuous)"
    )
    key_points: List[Dict[str, float]] = Field(
        default_factory=list,
        description="Key points the curve should pass through or near"
    )
    control_point_strategy: str = Field(
        default="auto",
        description="How to generate control points: 'auto', 'interpolate', 'approximate'"
    )
    additional_constraints: List[str] = Field(
        default_factory=list,
        description="Additional constraints: tangent directions, curvature requirements, etc."
    )


class CurveSpecialistAgent:
    """
    Agent specialized in generating curve-based designs.

    Capabilities:
    - B-Spline curve generation with proper knot vectors
    - NURBS curves with weight calculations for conic sections
    - Bezier curves with tangent continuity
    - Ellipses and elliptical arcs
    - Smooth interpolation through given points
    - Mixed curve/line designs

    Mathematical Foundation:
    - B-Spline: C(u) = Σ N_{i,p}(u) * P_i
    - NURBS: C(u) = Σ R_{i,p}(u) * P_i where R = weighted basis
    - Bezier: B(t) = Σ B_{i,n}(t) * P_i using Bernstein polynomials
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in parametric curve design for CAD systems.
Your specialty is generating mathematically precise curve definitions for:
- B-Splines (local control, arbitrary degree)
- NURBS (conic sections, weighted control)
- Bezier curves (endpoint interpolation, tangent control)
- Ellipses and elliptical arcs
- Mixed curve/linear designs

**Mathematical Foundations:**

1. **B-Spline Curves**
   - C(u) = Σ N(i,p)(u) * P_i
   - N(i,p)(u) are basis functions computed via Cox-de Boor recursion
   - Degree p curve needs at least p+1 control points
   - Local control: moving one point affects only nearby curve region
   - Continuity: C^(p-1) at simple knots

   Common applications:
   - CAM toolpaths, profile curves, smooth outlines
   - Default degree 3 (cubic) for most applications

2. **NURBS Curves**
   - C(u) = Σ R(i,p)(u) * P_i where R(i,p) = (N(i,p) * w_i) / Σ(N(j,p) * w_j)
   - Weights w_i control curve attraction to control points
   - w > 1: curve pulled toward point
   - w < 1: curve pushed away from point
   - Can exactly represent circles, ellipses, parabolas, hyperbolas

   Weight calculations for conics:
   - Circle/ellipse arc: middle weight = cos(half_angle)
   - Parabola: middle weight = 1.0 (non-rational degenerates to polynomial)

3. **Bezier Curves**
   - B(t) = Σ C(n,i) * (1-t)^(n-i) * t^i * P_i
   - Degree = num_points - 1
   - Always passes through first and last points
   - Tangent at endpoints: direction of first/last edge of control polygon

   Common types:
   - Quadratic (3 points): single bend
   - Cubic (4 points): S-curves, most flexible while stable

4. **Ellipses**
   - Parameterized: P(t) = center + a*cos(t)*major + b*sin(t)*minor
   - Ratio = minor_radius / major_radius
   - Full ellipse: t in [0, 2π]
   - Arc: t in [start_param, end_param]

**Design Guidelines:**

For smooth curves through points:
1. If points are sparse (< 10), use B-spline interpolation
2. If precise tangents needed, use cubic Bezier segments
3. If circular arcs needed, use NURBS with proper weights

For aerodynamic/organic shapes:
- Use cubic B-splines with evenly distributed control points
- Ensure curvature continuity (G2) at joints

For technical curves (cam profiles, gears):
- Consider using arcs + lines for simpler machining
- NURBS only if smooth transition is critical

**Output Format:**
Generate entities with all required mathematical parameters:
- Control points with precise coordinates
- Degree specification
- Knot vectors where applicable
- Weights for NURBS curves
- Proper layer organization

Always validate:
- Minimum control points for degree (n >= degree + 1)
- Positive weights for NURBS
- Proper knot vector length: n + degree + 2
"""),
            ("user", """Design requirement:
{user_input}

Intent analysis:
{intent}

Curve type hint: {curve_hint}

Generate the appropriate curve entities with mathematically correct parameters.""")
        ])

    def extract(self, user_input: str, intent: Dict[str, Any]) -> ExtendedEntities:
        """Extract curve entities from user input and parsed intent."""
        curve_hint = intent.get('curve_type_hint', 'bspline')

        structured_llm = self.llm.with_structured_output(ExtendedEntities)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "user_input": user_input,
            "intent": str(intent),
            "curve_hint": curve_hint
        })

        return result

    def create_interpolating_spline(
        self,
        points: List[Dict[str, float]],
        degree: int = 3,
        closed: bool = False
    ) -> Spline:
        """
        Create a B-spline that interpolates through given points.

        Uses chord-length parameterization for natural-looking curves.
        """
        if len(points) < degree + 1:
            degree = len(points) - 1

        point_objects = [Point(x=p['x'], y=p['y']) for p in points]

        return Spline(
            description="Interpolating B-spline",
            control_points=point_objects,  # Will use fit_points instead
            fit_points=point_objects,
            degree=degree,
            closed=closed,
            layer="Curves"
        )

    def create_bezier_from_tangents(
        self,
        start: Dict[str, float],
        end: Dict[str, float],
        start_tangent: Dict[str, float],
        end_tangent: Dict[str, float],
        tension: float = 0.33
    ) -> BezierCurve:
        """
        Create cubic Bezier curve from endpoints and tangent directions.

        Args:
            start: Start point {x, y}
            end: End point {x, y}
            start_tangent: Tangent direction at start {x, y} (will be normalized)
            end_tangent: Tangent direction at end {x, y} (will be normalized)
            tension: Scale factor for tangent length (default 1/3 of chord)
        """
        # Calculate chord length
        chord_length = math.sqrt(
            (end['x'] - start['x'])**2 +
            (end['y'] - start['y'])**2
        )

        # Normalize and scale tangents
        def normalize_scale(v: Dict[str, float], length: float) -> Dict[str, float]:
            mag = math.sqrt(v['x']**2 + v['y']**2)
            if mag < 1e-10:
                return {'x': 0, 'y': 0}
            scale = length / mag
            return {'x': v['x'] * scale, 'y': v['y'] * scale}

        tangent_length = chord_length * tension
        t0 = normalize_scale(start_tangent, tangent_length)
        t1 = normalize_scale(end_tangent, tangent_length)

        # Control points
        p0 = Point(x=start['x'], y=start['y'])
        p1 = Point(x=start['x'] + t0['x'], y=start['y'] + t0['y'])
        p2 = Point(x=end['x'] - t1['x'], y=end['y'] - t1['y'])
        p3 = Point(x=end['x'], y=end['y'])

        return BezierCurve(
            description="Cubic Bezier from tangents",
            control_points=[p0, p1, p2, p3],
            layer="Curves"
        )

    def create_nurbs_arc(
        self,
        center: Dict[str, float],
        radius: float,
        start_angle: float,
        end_angle: float
    ) -> NURBSCurve:
        """
        Create NURBS representation of a circular arc.

        Uses standard 3-point rational quadratic representation.
        Arc must be <= 180 degrees; larger arcs need multiple segments.

        Mathematical basis:
        - Start and end points have weight 1.0
        - Middle control point is at intersection of tangent lines
        - Middle weight = cos(half_angle)
        """
        # Ensure arc is <= 180 degrees
        arc_angle = end_angle - start_angle
        if arc_angle < 0:
            arc_angle += 2 * math.pi

        if arc_angle > math.pi:
            # Need to split into two arcs - for now, clamp to 180
            arc_angle = math.pi
            end_angle = start_angle + math.pi

        half_angle = arc_angle / 2
        mid_angle = start_angle + half_angle

        # Start point
        p0 = ControlPoint(
            x=center['x'] + radius * math.cos(start_angle),
            y=center['y'] + radius * math.sin(start_angle),
            weight=1.0
        )

        # End point
        p2 = ControlPoint(
            x=center['x'] + radius * math.cos(end_angle),
            y=center['y'] + radius * math.sin(end_angle),
            weight=1.0
        )

        # Middle control point (on tangent lines intersection)
        # Distance from center to middle control point
        d = radius / math.cos(half_angle)
        p1 = ControlPoint(
            x=center['x'] + d * math.cos(mid_angle),
            y=center['y'] + d * math.sin(mid_angle),
            weight=math.cos(half_angle)
        )

        return NURBSCurve(
            description=f"NURBS arc {math.degrees(arc_angle):.1f} degrees",
            control_points=[p0, p1, p2],
            degree=2,
            knots=[0, 0, 0, 1, 1, 1],
            layer="Curves"
        )

    def create_ellipse(
        self,
        center: Dict[str, float],
        major_radius: float,
        minor_radius: float,
        rotation: float = 0,
        start_param: float = 0,
        end_param: float = 2 * math.pi
    ) -> Ellipse:
        """
        Create an ellipse or elliptical arc.

        Args:
            center: Center point
            major_radius: Semi-major axis length
            minor_radius: Semi-minor axis length
            rotation: Rotation angle of major axis (radians)
            start_param: Start parameter (0 = major axis direction)
            end_param: End parameter
        """
        # Major axis vector
        major_x = major_radius * math.cos(rotation)
        major_y = major_radius * math.sin(rotation)

        ratio = minor_radius / major_radius if major_radius > 0 else 1.0

        return Ellipse(
            description="Ellipse" if abs(end_param - start_param - 2*math.pi) < 0.01 else "Elliptical arc",
            center_x=center['x'],
            center_y=center['y'],
            major_axis_x=major_x,
            major_axis_y=major_y,
            ratio=ratio,
            start_param=start_param,
            end_param=end_param,
            layer="Curves"
        )

    def create_smooth_polyline(
        self,
        vertices: List[Dict[str, float]],
        closed: bool = False,
        corner_radius: float = 0
    ) -> PolylineWithCurves:
        """
        Create a polyline with smooth corners using bulge values.

        If corner_radius > 0, creates rounded corners using arc segments.

        Bulge calculation:
        bulge = tan(arc_angle / 4)
        For a quarter circle (90°): bulge ≈ 0.414
        For a semicircle (180°): bulge = 1.0
        """
        processed_vertices = []

        if corner_radius <= 0:
            # No rounding - just straight segments
            for v in vertices:
                processed_vertices.append({
                    'x': v['x'],
                    'y': v['y'],
                    'bulge': 0
                })
        else:
            # Add rounded corners
            n = len(vertices)
            for i in range(n):
                curr = vertices[i]

                if not closed and (i == 0 or i == n - 1):
                    # First and last vertices of open polyline - no rounding
                    processed_vertices.append({
                        'x': curr['x'],
                        'y': curr['y'],
                        'bulge': 0
                    })
                else:
                    # Calculate corner angle
                    prev = vertices[(i - 1) % n]
                    next_v = vertices[(i + 1) % n]

                    # Vectors
                    v1 = {'x': curr['x'] - prev['x'], 'y': curr['y'] - prev['y']}
                    v2 = {'x': next_v['x'] - curr['x'], 'y': next_v['y'] - curr['y']}

                    # Normalize
                    len1 = math.sqrt(v1['x']**2 + v1['y']**2)
                    len2 = math.sqrt(v2['x']**2 + v2['y']**2)

                    if len1 < 1e-10 or len2 < 1e-10:
                        processed_vertices.append({
                            'x': curr['x'],
                            'y': curr['y'],
                            'bulge': 0
                        })
                        continue

                    v1 = {'x': v1['x']/len1, 'y': v1['y']/len1}
                    v2 = {'x': v2['x']/len2, 'y': v2['y']/len2}

                    # Angle between edges
                    dot = v1['x']*v2['x'] + v1['y']*v2['y']
                    angle = math.acos(max(-1, min(1, dot)))

                    # Offset distance along edges
                    offset = corner_radius / math.tan(angle / 2) if angle > 0.01 else 0
                    offset = min(offset, len1 * 0.4, len2 * 0.4)

                    # Arc start point
                    arc_start = {
                        'x': curr['x'] - v1['x'] * offset,
                        'y': curr['y'] - v1['y'] * offset
                    }

                    # Arc end point
                    arc_end = {
                        'x': curr['x'] + v2['x'] * offset,
                        'y': curr['y'] + v2['y'] * offset
                    }

                    # Bulge for the arc
                    arc_angle = math.pi - angle
                    bulge = math.tan(arc_angle / 4)

                    # Determine sign based on turn direction
                    cross = v1['x'] * v2['y'] - v1['y'] * v2['x']
                    if cross < 0:
                        bulge = -bulge

                    # Add arc start point with bulge
                    processed_vertices.append({
                        'x': arc_start['x'],
                        'y': arc_start['y'],
                        'bulge': bulge
                    })

                    # Arc end point will be handled by next iteration or closing

        return PolylineWithCurves(
            description="Smooth polyline with curved corners",
            vertices=processed_vertices,
            closed=closed,
            layer="Curves"
        )
