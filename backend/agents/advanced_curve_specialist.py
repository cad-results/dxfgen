"""
Advanced Curve Specialist Agent - Expert in complex nonlinear designs.

Handles sophisticated designs requiring:
- B-Spline curves for smooth profiles (fuselages, organic shapes)
- NURBS for precise conic sections (circles, ellipses in aerospace)
- Bezier curves for decorative elements
- Complex multi-component assemblies
- Real-world product reproductions
- Iconic structures (spacecraft, castles, vehicles)
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .curve_entities import (
    Spline, NURBSCurve, BezierCurve, Ellipse,
    PolylineWithCurves, ExtendedEntities, Point, ControlPoint
)
from .entity_extractor import Line, Circle, Arc, Polyline, Hatch
from .research_agent import ResearchAgent


class ComponentBreakdown(BaseModel):
    """Breakdown of a complex design into drawable components."""
    component_name: str
    curve_type: str  # line, circle, arc, bspline, nurbs, bezier, ellipse
    key_dimensions: Dict[str, float]
    control_points: Optional[List[Dict[str, float]]] = None
    position: Dict[str, float]  # x, y offset from origin
    layer: str


class ComplexDesignPlan(BaseModel):
    """Plan for drawing a complex design."""
    design_name: str
    total_width: float
    total_height: float
    scale_factor: float = 1.0
    components: List[ComponentBreakdown]
    notes: str = ""


class AdvancedCurveSpecialistAgent:
    """
    Advanced agent for complex curve-based designs.

    Specializes in:
    1. Spacecraft and aerospace (Saturn V, rockets, aircraft)
    2. Architecture (castles, monuments, theme parks)
    3. Industrial products (precise part drawings)
    4. Vehicles (cars, trains, ships)
    5. Organic/artistic shapes
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.research_agent = ResearchAgent(llm)

        self.system_prompt = """You are an expert CAD engineer specializing in complex curve-based designs.
Your expertise covers aerospace, architecture, industrial design, and artistic forms.

**Your Capabilities:**

1. **Curve Type Selection** - Choose the optimal curve for each element:
   - **Lines**: Straight edges, structural elements, grids
   - **Arcs**: Circular sections, simple curves, door swings
   - **Circles**: Wheels, ports, holes, cylindrical cross-sections
   - **Ellipses**: Oval shapes, angled circular views, aerodynamic forms
   - **B-Splines**: Complex smooth profiles, fuselage shapes, organic contours
   - **NURBS**: Precise conic sections, exact circles/ellipses, aerospace curves
   - **Bezier**: Decorative curves, simple smooth transitions, logos
   - **Polylines with bulge**: Mixed straight/curved paths, efficient profiles

2. **Complex Structure Decomposition**:
   Break down complex objects into drawable components:

   *Spacecraft (e.g., Saturn V)*:
   - Command module: NURBS ogive shape
   - Service module: Cylinder (circle cross-section, line profile)
   - Stages: Tapered cylinders, use B-spline for fairings
   - Engines: Circles for bells, lines for structure
   - Fins: Polylines with curved leading edges

   *Castles (e.g., Cinderella Castle)*:
   - Towers: Circles/ellipses for round towers
   - Spires: B-spline for Gothic curves
   - Arches: NURBS for precise gothic arches
   - Battlements: Polylines for crenellations
   - Windows: Ellipses and arcs

   *Industrial Parts*:
   - Beams: Lines and rectangles
   - Holes: Circles at precise positions
   - Rounded corners: Arcs or NURBS
   - Profiles: B-spline for complex cross-sections
   - Slots: Polylines with arc ends

3. **Dimensional Accuracy**:
   - Always work in millimeters (mm)
   - Use precise control points for curves
   - Maintain proportional relationships
   - Apply appropriate scale factors

4. **Layer Organization**:
   - Group related elements by function
   - Use descriptive layer names
   - Separate construction lines from final geometry

**Mathematical Precision for Curves:**

*B-Spline Control Points*:
For a smooth profile, distribute control points to define the shape:
- More points = more local control
- Degree 3 (cubic) is standard for smooth curves
- Points should follow the desired curve outline

*NURBS Weights*:
- Weight = 1.0 for standard points
- Increase weight to pull curve toward point
- For circular arcs: middle weight = cos(half_angle)

*Bezier Tangents*:
- Start tangent: direction leaving first point
- End tangent: direction entering last point
- Tangent magnitude affects curve "tightness"

**Output Format:**
Generate entities with precise coordinates and proper curve parameters.
All dimensions in mm. Include layer assignments."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", """Design Request: {user_input}

Research Data:
{research_data}

Intent Analysis:
{intent}

Scale: {scale} (1.0 = actual size, adjust for drawing)

Generate all geometric entities needed for this design.
Use appropriate curve types for each component.
Ensure mathematical accuracy in all parameters.""")
        ])

    def extract(self, user_input: str, intent: Dict[str, Any]) -> ExtendedEntities:
        """Extract entities with research support for complex designs."""

        # Determine if research is needed
        needs_research = self._needs_research(user_input, intent)

        research_data = {}
        if needs_research:
            research_data = self.research_agent.research_with_fallback(
                user_input,
                str(intent)
            )

        # Determine appropriate scale
        scale = self._determine_scale(user_input, research_data, intent)

        # Generate entities
        structured_llm = self.llm.with_structured_output(ExtendedEntities)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "user_input": user_input,
            "research_data": str(research_data),
            "intent": str(intent),
            "scale": scale
        })

        return result

    def _needs_research(self, user_input: str, intent: Dict[str, Any]) -> bool:
        """Determine if web research is needed."""
        research_keywords = [
            # Product references
            "global industrial", "part number", "model", "sku",
            "replacement", "specification", "partstown",
            # Famous structures
            "saturn v", "apollo", "space shuttle", "rocket",
            "cinderella castle", "disney", "neuschwanstein",
            "eiffel tower", "statue of liberty",
            # Vehicles
            "boeing", "airbus", "f1 car", "formula 1",
            "ferrari", "lamborghini", "747", "a380",
            # Specific products
            "160cp19", "168255", "beam", "noseplate",
            "garland", "true", "hoshizaki", "manitowoc", "vulcan"
        ]

        input_lower = user_input.lower()
        return any(kw in input_lower for kw in research_keywords)

    def _determine_scale(self, user_input: str, research_data: Dict, intent: Dict) -> float:
        """Determine appropriate scale factor for drawing."""
        input_lower = user_input.lower()

        # Check for explicit scale requests
        if "1:1" in input_lower or "full scale" in input_lower or "actual size" in input_lower:
            return 1.0
        if "1:10" in input_lower:
            return 0.1
        if "1:100" in input_lower:
            return 0.01
        if "1:1000" in input_lower:
            return 0.001

        # Auto-scale based on object type
        if research_data and "specifications" in research_data:
            specs = research_data["specifications"]
            dims = specs.get("dimensions", {})

            # Find maximum dimension
            max_dim = max(dims.values()) if dims else 0

            if max_dim > 100000:  # > 100 meters (spacecraft)
                return 0.001  # 1:1000
            elif max_dim > 10000:  # > 10 meters (buildings)
                return 0.01  # 1:100
            elif max_dim > 1000:  # > 1 meter (furniture, large equipment)
                return 0.1  # 1:10
            else:
                return 1.0  # Actual size for small parts

        # Default based on keywords
        if any(kw in input_lower for kw in ["rocket", "spacecraft", "building", "castle"]):
            return 0.01
        elif any(kw in input_lower for kw in ["vehicle", "car", "aircraft"]):
            return 0.05
        else:
            return 1.0

    def create_saturn_v(self, scale: float = 0.01, detail_level: str = "medium") -> ExtendedEntities:
        """Generate Saturn V rocket profile.

        Args:
            scale: Scale factor (0.01 = 1:100)
            detail_level: 'low', 'medium', or 'high' for amount of detail
        """
        s = scale  # Scale factor

        entities = ExtendedEntities()

        # Stage 1 (S-IC) - Bottom
        stage1_height = 42100 * s
        stage1_diameter = 10100 * s

        # Stage 1 cylinder outline (left side)
        entities.lines.append(Line(
            description="S-IC left edge",
            x1=0, y1=0,
            x2=0, y2=stage1_height,
            layer="Stage1"
        ))

        # Stage 1 cylinder outline (right side)
        entities.lines.append(Line(
            description="S-IC right edge",
            x1=stage1_diameter, y1=0,
            x2=stage1_diameter, y2=stage1_height,
            layer="Stage1"
        ))

        # Stage 1 bottom
        entities.lines.append(Line(
            description="S-IC bottom",
            x1=0, y1=0,
            x2=stage1_diameter, y2=0,
            layer="Stage1"
        ))

        # F-1 engine bells (5 engines)
        engine_bell_diameter = 3760 * s
        engine_positions = [
            stage1_diameter / 2,  # Center
            stage1_diameter * 0.25,  # Inner left
            stage1_diameter * 0.75,  # Inner right
            stage1_diameter * 0.1,   # Outer left
            stage1_diameter * 0.9,   # Outer right
        ]

        for i, x_pos in enumerate(engine_positions):
            entities.circles.append(Circle(
                description=f"F-1 Engine {i+1}",
                center_x=x_pos,
                center_y=-engine_bell_diameter/2,
                radius=engine_bell_diameter/2,
                layer="Engines"
            ))

        # Fins (4 fins, show 2 visible)
        fin_span = 5600 * s
        fin_height = 7000 * s
        for side in [-1, 1]:  # Left and right
            x_base = stage1_diameter/2 + side * stage1_diameter/2
            entities.polylines.append(Polyline(
                description=f"Fin {'left' if side < 0 else 'right'}",
                points=[
                    Point(x=x_base, y=0),
                    Point(x=x_base + side * fin_span/2, y=fin_height * 0.3),
                    Point(x=x_base + side * fin_span/2, y=fin_height),
                    Point(x=x_base, y=fin_height),
                ],
                closed=True,
                layer="Fins"
            ))

        # Stage 2 (S-II)
        stage2_height = 24900 * s
        y_offset = stage1_height

        # Interstage taper (B-spline for smooth transition)
        entities.splines.append(Spline(
            description="S-IC to S-II interstage left",
            control_points=[
                Point(x=0, y=y_offset),
                Point(x=0, y=y_offset + 1000*s),
                Point(x=100*s, y=y_offset + 2000*s),
                Point(x=0, y=y_offset + 3000*s),
            ],
            degree=3,
            layer="Interstage"
        ))

        entities.lines.append(Line(
            description="S-II left edge",
            x1=0, y1=y_offset + 3000*s,
            x2=0, y2=y_offset + stage2_height,
            layer="Stage2"
        ))

        entities.lines.append(Line(
            description="S-II right edge",
            x1=stage1_diameter, y1=y_offset + 3000*s,
            x2=stage1_diameter, y2=y_offset + stage2_height,
            layer="Stage2"
        ))

        # Stage 3 (S-IVB) - Narrower
        stage3_height = 17900 * s
        stage3_diameter = 6600 * s
        y_offset += stage2_height
        x_offset = (stage1_diameter - stage3_diameter) / 2

        # Taper from S-II to S-IVB (B-spline)
        entities.splines.append(Spline(
            description="S-II to S-IVB taper left",
            control_points=[
                Point(x=0, y=y_offset),
                Point(x=x_offset * 0.5, y=y_offset + 1000*s),
                Point(x=x_offset, y=y_offset + 2000*s),
            ],
            degree=2,
            layer="Interstage"
        ))

        entities.lines.append(Line(
            description="S-IVB left edge",
            x1=x_offset, y1=y_offset + 2000*s,
            x2=x_offset, y2=y_offset + stage3_height,
            layer="Stage3"
        ))

        entities.lines.append(Line(
            description="S-IVB right edge",
            x1=x_offset + stage3_diameter, y1=y_offset + 2000*s,
            x2=x_offset + stage3_diameter, y2=y_offset + stage3_height,
            layer="Stage3"
        ))

        # Command/Service Module
        y_offset += stage3_height
        cm_height = 3200 * s
        cm_diameter = 3900 * s
        cm_x_offset = (stage1_diameter - cm_diameter) / 2

        # Command Module (ogive shape using NURBS)
        entities.nurbs_curves.append(NURBSCurve(
            description="Command Module profile",
            control_points=[
                ControlPoint(x=cm_x_offset, y=y_offset, weight=1.0),
                ControlPoint(x=cm_x_offset - 200*s, y=y_offset + cm_height*0.3, weight=0.85),
                ControlPoint(x=cm_x_offset, y=y_offset + cm_height*0.8, weight=0.9),
                ControlPoint(x=cm_x_offset + cm_diameter/2, y=y_offset + cm_height, weight=1.0),
            ],
            degree=3,
            layer="CommandModule"
        ))

        # Launch Escape Tower
        tower_height = 10100 * s
        tower_base = cm_x_offset + cm_diameter/2
        y_offset += cm_height

        entities.lines.append(Line(
            description="Escape tower",
            x1=tower_base, y1=y_offset,
            x2=tower_base, y2=y_offset + tower_height,
            layer="EscapeTower"
        ))

        # Tower lattice structure (simplified)
        for i in range(4):
            y_pos = y_offset + i * tower_height / 4
            entities.lines.append(Line(
                description=f"Tower strut {i+1}",
                x1=tower_base - 500*s, y1=y_pos,
                x2=tower_base, y2=y_pos + tower_height/4,
                layer="EscapeTower"
            ))

        entities.notes = f"Saturn V rocket profile at 1:{int(1/scale)} scale"
        return entities

    def create_industrial_beam(self, length_mm: float = 1066.8, height_mm: float = 76.2,
                               hole_spacing: float = 50.8, hole_diameter: float = 11.0,
                               specifications: Dict[str, Any] = None) -> ExtendedEntities:
        """Generate industrial double rivet beam profile.

        Args:
            length_mm: Beam length (default 42" = 1066.8mm)
            height_mm: Beam height (default 3" = 76.2mm)
            hole_spacing: Distance between holes (default 2" = 50.8mm)
            hole_diameter: Rivet hole diameter (default 11mm)
            specifications: Optional specs from research
        """
        # Override with specs if provided
        if specifications:
            dims = specifications.get("dimensions", {})
            length_mm = dims.get("length", length_mm)
            height_mm = dims.get("height", height_mm)
            hole_spacing = dims.get("hole_spacing", hole_spacing)
            hole_diameter = dims.get("hole_diameter", hole_diameter)
        entities = ExtendedEntities()

        # Beam outline
        entities.polylines.append(Polyline(
            description="Beam outline",
            points=[
                Point(x=0, y=0),
                Point(x=length_mm, y=0),
                Point(x=length_mm, y=height_mm),
                Point(x=0, y=height_mm),
            ],
            closed=True,
            layer="Outline"
        ))

        # Rivet holes (double row)
        row1_y = height_mm * 0.25
        row2_y = height_mm * 0.75
        end_clearance = hole_spacing / 2

        x = end_clearance
        while x < length_mm - end_clearance:
            # Top row
            entities.circles.append(Circle(
                description=f"Rivet hole top at x={x:.1f}",
                center_x=x, center_y=row1_y,
                radius=hole_diameter/2,
                layer="Holes"
            ))
            # Bottom row
            entities.circles.append(Circle(
                description=f"Rivet hole bottom at x={x:.1f}",
                center_x=x, center_y=row2_y,
                radius=hole_diameter/2,
                layer="Holes"
            ))
            x += hole_spacing

        # Step profile (characteristic of rivet beams)
        step_depth = height_mm * 0.15
        entities.lines.append(Line(
            description="Step line top",
            x1=0, y1=height_mm - step_depth,
            x2=length_mm, y2=height_mm - step_depth,
            layer="Detail"
        ))
        entities.lines.append(Line(
            description="Step line bottom",
            x1=0, y1=step_depth,
            x2=length_mm, y2=step_depth,
            layer="Detail"
        ))

        entities.notes = f"Double rivet beam: {length_mm}mm x {height_mm}mm, {hole_spacing}mm hole spacing"
        return entities

    def create_noseplate(self, width_mm: float = 457.2, height_mm: float = 355.6,
                         corner_radius: float = 25.4, hole_diameter: float = 9.5,
                         specifications: Dict[str, Any] = None) -> ExtendedEntities:
        """Generate hand truck noseplate with rounded corners.

        Args:
            width_mm: Plate width (default 18" = 457.2mm)
            height_mm: Plate height/depth (default 14" = 355.6mm)
            corner_radius: Radius of rounded corners (default 1" = 25.4mm)
            hole_diameter: Mounting hole diameter (default 9.5mm)
            specifications: Optional specs from research
        """
        # Override with specs if provided
        if specifications:
            dims = specifications.get("dimensions", {})
            width_mm = dims.get("width", width_mm)
            height_mm = dims.get("height", height_mm)
            corner_radius = dims.get("corner_radius", corner_radius)
            hole_diameter = dims.get("hole_diameter", hole_diameter)

        depth_mm = height_mm  # Alias for existing code
        entities = ExtendedEntities()

        # Main plate with rounded corners using NURBS arcs
        # Bottom left corner
        entities.nurbs_curves.append(NURBSCurve(
            description="Bottom left corner",
            control_points=[
                ControlPoint(x=0, y=corner_radius, weight=1.0),
                ControlPoint(x=0, y=0, weight=math.cos(math.pi/4)),
                ControlPoint(x=corner_radius, y=0, weight=1.0),
            ],
            degree=2,
            knots=[0, 0, 0, 1, 1, 1],
            layer="Outline"
        ))

        # Bottom edge
        entities.lines.append(Line(
            description="Bottom edge",
            x1=corner_radius, y1=0,
            x2=width_mm - corner_radius, y2=0,
            layer="Outline"
        ))

        # Bottom right corner
        entities.nurbs_curves.append(NURBSCurve(
            description="Bottom right corner",
            control_points=[
                ControlPoint(x=width_mm - corner_radius, y=0, weight=1.0),
                ControlPoint(x=width_mm, y=0, weight=math.cos(math.pi/4)),
                ControlPoint(x=width_mm, y=corner_radius, weight=1.0),
            ],
            degree=2,
            knots=[0, 0, 0, 1, 1, 1],
            layer="Outline"
        ))

        # Right edge
        entities.lines.append(Line(
            description="Right edge",
            x1=width_mm, y1=corner_radius,
            x2=width_mm, y2=depth_mm - corner_radius,
            layer="Outline"
        ))

        # Top right corner
        entities.nurbs_curves.append(NURBSCurve(
            description="Top right corner",
            control_points=[
                ControlPoint(x=width_mm, y=depth_mm - corner_radius, weight=1.0),
                ControlPoint(x=width_mm, y=depth_mm, weight=math.cos(math.pi/4)),
                ControlPoint(x=width_mm - corner_radius, y=depth_mm, weight=1.0),
            ],
            degree=2,
            knots=[0, 0, 0, 1, 1, 1],
            layer="Outline"
        ))

        # Top edge
        entities.lines.append(Line(
            description="Top edge",
            x1=width_mm - corner_radius, y1=depth_mm,
            x2=corner_radius, y2=depth_mm,
            layer="Outline"
        ))

        # Top left corner
        entities.nurbs_curves.append(NURBSCurve(
            description="Top left corner",
            control_points=[
                ControlPoint(x=corner_radius, y=depth_mm, weight=1.0),
                ControlPoint(x=0, y=depth_mm, weight=math.cos(math.pi/4)),
                ControlPoint(x=0, y=depth_mm - corner_radius, weight=1.0),
            ],
            degree=2,
            knots=[0, 0, 0, 1, 1, 1],
            layer="Outline"
        ))

        # Left edge
        entities.lines.append(Line(
            description="Left edge",
            x1=0, y1=depth_mm - corner_radius,
            x2=0, y2=corner_radius,
            layer="Outline"
        ))

        # Mounting holes
        hole_inset = 25.4  # 1 inch from edge
        entities.circles.append(Circle(
            description="Mounting hole left",
            center_x=hole_inset, center_y=depth_mm/2,
            radius=hole_diameter/2,
            layer="Holes"
        ))
        entities.circles.append(Circle(
            description="Mounting hole right",
            center_x=width_mm - hole_inset, center_y=depth_mm/2,
            radius=hole_diameter/2,
            layer="Holes"
        ))

        # Reinforcement rib (center line)
        entities.lines.append(Line(
            description="Center reinforcement rib",
            x1=width_mm/2, y1=corner_radius,
            x2=width_mm/2, y2=depth_mm - corner_radius,
            layer="Detail"
        ))

        entities.notes = f"Noseplate: {width_mm}mm x {depth_mm}mm with {corner_radius}mm radius corners"
        return entities

    def create_castle_silhouette(self, scale: float = 0.01, detail_level: str = "medium") -> ExtendedEntities:
        """Generate Disney-style castle silhouette.

        Args:
            scale: Scale factor (0.01 = 1:100)
            detail_level: 'low', 'medium', or 'high' for amount of detail
        """
        s = scale
        entities = ExtendedEntities()

        # Base structure
        base_width = 30000 * s
        base_height = 20000 * s

        # Main keep
        entities.polylines.append(Polyline(
            description="Castle base",
            points=[
                Point(x=0, y=0),
                Point(x=base_width, y=0),
                Point(x=base_width, y=base_height),
                Point(x=0, y=base_height),
            ],
            closed=True,
            layer="Base"
        ))

        # Central tower (tall spire)
        tower_width = 8000 * s
        tower_height = 48000 * s
        tower_x = base_width/2 - tower_width/2

        # Tower body
        entities.lines.append(Line(
            description="Central tower left",
            x1=tower_x, y1=base_height,
            x2=tower_x, y2=base_height + tower_height * 0.6,
            layer="MainTower"
        ))
        entities.lines.append(Line(
            description="Central tower right",
            x1=tower_x + tower_width, y1=base_height,
            x2=tower_x + tower_width, y2=base_height + tower_height * 0.6,
            layer="MainTower"
        ))

        # Spire (B-spline for Gothic curve)
        spire_top = base_height + tower_height
        spire_base = base_height + tower_height * 0.6
        entities.splines.append(Spline(
            description="Central spire left",
            control_points=[
                Point(x=tower_x, y=spire_base),
                Point(x=tower_x + tower_width*0.1, y=spire_base + (spire_top-spire_base)*0.3),
                Point(x=tower_x + tower_width*0.3, y=spire_base + (spire_top-spire_base)*0.7),
                Point(x=tower_x + tower_width/2, y=spire_top),
            ],
            degree=3,
            layer="Spire"
        ))
        entities.splines.append(Spline(
            description="Central spire right",
            control_points=[
                Point(x=tower_x + tower_width, y=spire_base),
                Point(x=tower_x + tower_width*0.9, y=spire_base + (spire_top-spire_base)*0.3),
                Point(x=tower_x + tower_width*0.7, y=spire_base + (spire_top-spire_base)*0.7),
                Point(x=tower_x + tower_width/2, y=spire_top),
            ],
            degree=3,
            layer="Spire"
        ))

        # Secondary turrets (4 smaller ones)
        turret_positions = [
            (base_width * 0.1, base_height),
            (base_width * 0.3, base_height),
            (base_width * 0.7, base_height),
            (base_width * 0.9, base_height),
        ]
        turret_diameter = 3000 * s
        turret_height = 12000 * s

        for i, (tx, ty) in enumerate(turret_positions):
            # Turret base (cylindrical)
            entities.ellipses.append(Ellipse(
                description=f"Turret {i+1} base",
                center_x=tx, center_y=ty + turret_height * 0.6,
                major_axis_x=turret_diameter/2, major_axis_y=0,
                ratio=0.3,  # Perspective effect
                layer="Turrets"
            ))

            # Turret conical roof
            entities.splines.append(Spline(
                description=f"Turret {i+1} roof",
                control_points=[
                    Point(x=tx - turret_diameter/2, y=ty + turret_height * 0.6),
                    Point(x=tx - turret_diameter/4, y=ty + turret_height * 0.8),
                    Point(x=tx, y=ty + turret_height),
                    Point(x=tx + turret_diameter/4, y=ty + turret_height * 0.8),
                    Point(x=tx + turret_diameter/2, y=ty + turret_height * 0.6),
                ],
                degree=3,
                layer="Turrets"
            ))

        # Gothic arched entrance
        arch_width = 7000 * s
        arch_height = 10000 * s
        arch_x = base_width/2 - arch_width/2

        # Arch using NURBS for precise pointed arch
        entities.nurbs_curves.append(NURBSCurve(
            description="Gothic arch",
            control_points=[
                ControlPoint(x=arch_x, y=0, weight=1.0),
                ControlPoint(x=arch_x, y=arch_height * 0.7, weight=1.0),
                ControlPoint(x=arch_x + arch_width/2, y=arch_height * 1.2, weight=0.7),
                ControlPoint(x=arch_x + arch_width, y=arch_height * 0.7, weight=1.0),
                ControlPoint(x=arch_x + arch_width, y=0, weight=1.0),
            ],
            degree=3,
            layer="Entrance"
        ))

        # Decorative windows (ellipses)
        window_positions = [
            (base_width * 0.25, base_height * 0.6),
            (base_width * 0.75, base_height * 0.6),
            (tower_x + tower_width/2, base_height + tower_height * 0.3),
        ]

        for i, (wx, wy) in enumerate(window_positions):
            entities.ellipses.append(Ellipse(
                description=f"Window {i+1}",
                center_x=wx, center_y=wy,
                major_axis_x=1500*s, major_axis_y=0,
                ratio=1.5,  # Tall Gothic window
                layer="Windows"
            ))

        # Battlements (crenellations)
        merlon_width = 1000 * s
        crenel_width = 800 * s
        merlon_height = 1500 * s

        x = 0
        while x < base_width:
            if x + merlon_width <= base_width:
                entities.polylines.append(Polyline(
                    description="Battlement merlon",
                    points=[
                        Point(x=x, y=base_height),
                        Point(x=x, y=base_height + merlon_height),
                        Point(x=x + merlon_width, y=base_height + merlon_height),
                        Point(x=x + merlon_width, y=base_height),
                    ],
                    closed=False,
                    layer="Battlements"
                ))
            x += merlon_width + crenel_width

        entities.notes = f"Disney-style castle silhouette at 1:{int(1/scale)} scale"
        return entities

    def create_princess_dress(self, scale: float = 1.0, style: str = "generic") -> ExtendedEntities:
        """Generate princess ball gown silhouette using smooth B-splines.

        Args:
            scale: Scale factor
            style: 'cinderella', 'belle', 'aurora', or 'generic'
        """
        s = scale
        entities = ExtendedEntities()

        # Dress dimensions (based on style)
        if style == "cinderella":
            # Cinderella's iconic silver-blue ball gown
            bodice_height = 250 * s
            waist_width = 180 * s
            skirt_height = 600 * s
            skirt_width = 800 * s
            puff_size = 80 * s
        elif style == "belle":
            # Belle's golden ball gown
            bodice_height = 230 * s
            waist_width = 170 * s
            skirt_height = 650 * s
            skirt_width = 900 * s
            puff_size = 100 * s
        else:
            # Generic princess dress
            bodice_height = 240 * s
            waist_width = 175 * s
            skirt_height = 620 * s
            skirt_width = 850 * s
            puff_size = 90 * s

        center_x = skirt_width / 2

        # Neckline (sweetheart or off-shoulder using B-spline)
        neckline_y = bodice_height + skirt_height
        entities.splines.append(Spline(
            description="Neckline curve",
            control_points=[
                Point(x=center_x - waist_width/2 - puff_size, y=neckline_y),
                Point(x=center_x - waist_width/3, y=neckline_y + 20*s),
                Point(x=center_x, y=neckline_y - 30*s),  # Sweetheart dip
                Point(x=center_x + waist_width/3, y=neckline_y + 20*s),
                Point(x=center_x + waist_width/2 + puff_size, y=neckline_y),
            ],
            degree=3,
            layer="Bodice"
        ))

        # Puffy sleeves (left)
        sleeve_top_y = neckline_y - 30*s
        entities.splines.append(Spline(
            description="Left sleeve puff",
            control_points=[
                Point(x=center_x - waist_width/2 - puff_size, y=neckline_y),
                Point(x=center_x - waist_width/2 - puff_size*1.5, y=neckline_y - 50*s),
                Point(x=center_x - waist_width/2 - puff_size*1.8, y=neckline_y - 100*s),
                Point(x=center_x - waist_width/2 - puff_size*1.3, y=neckline_y - 140*s),
                Point(x=center_x - waist_width/2 - puff_size*0.5, y=neckline_y - 120*s),
            ],
            degree=3,
            layer="Sleeves"
        ))

        # Puffy sleeves (right)
        entities.splines.append(Spline(
            description="Right sleeve puff",
            control_points=[
                Point(x=center_x + waist_width/2 + puff_size, y=neckline_y),
                Point(x=center_x + waist_width/2 + puff_size*1.5, y=neckline_y - 50*s),
                Point(x=center_x + waist_width/2 + puff_size*1.8, y=neckline_y - 100*s),
                Point(x=center_x + waist_width/2 + puff_size*1.3, y=neckline_y - 140*s),
                Point(x=center_x + waist_width/2 + puff_size*0.5, y=neckline_y - 120*s),
            ],
            degree=3,
            layer="Sleeves"
        ))

        # Bodice sides (fitted, slight curve)
        waist_y = skirt_height
        entities.splines.append(Spline(
            description="Bodice left side",
            control_points=[
                Point(x=center_x - waist_width/2 - puff_size*0.5, y=neckline_y - 120*s),
                Point(x=center_x - waist_width/2 - 20*s, y=neckline_y - bodice_height*0.5),
                Point(x=center_x - waist_width/2, y=waist_y),
            ],
            degree=2,
            layer="Bodice"
        ))

        entities.splines.append(Spline(
            description="Bodice right side",
            control_points=[
                Point(x=center_x + waist_width/2 + puff_size*0.5, y=neckline_y - 120*s),
                Point(x=center_x + waist_width/2 + 20*s, y=neckline_y - bodice_height*0.5),
                Point(x=center_x + waist_width/2, y=waist_y),
            ],
            degree=2,
            layer="Bodice"
        ))

        # Ball gown skirt (dramatic flowing curves)
        # Left side of skirt
        entities.splines.append(Spline(
            description="Skirt left flowing curve",
            control_points=[
                Point(x=center_x - waist_width/2, y=waist_y),
                Point(x=center_x - waist_width/2 - 50*s, y=waist_y - 100*s),
                Point(x=center_x - skirt_width*0.35, y=waist_y - skirt_height*0.4),
                Point(x=center_x - skirt_width*0.45, y=waist_y - skirt_height*0.7),
                Point(x=center_x - skirt_width/2, y=0),
            ],
            degree=3,
            layer="Skirt"
        ))

        # Right side of skirt
        entities.splines.append(Spline(
            description="Skirt right flowing curve",
            control_points=[
                Point(x=center_x + waist_width/2, y=waist_y),
                Point(x=center_x + waist_width/2 + 50*s, y=waist_y - 100*s),
                Point(x=center_x + skirt_width*0.35, y=waist_y - skirt_height*0.4),
                Point(x=center_x + skirt_width*0.45, y=waist_y - skirt_height*0.7),
                Point(x=center_x + skirt_width/2, y=0),
            ],
            degree=3,
            layer="Skirt"
        ))

        # Hem with gentle waves
        entities.splines.append(Spline(
            description="Skirt hem",
            control_points=[
                Point(x=center_x - skirt_width/2, y=0),
                Point(x=center_x - skirt_width*0.35, y=20*s),
                Point(x=center_x - skirt_width*0.2, y=-10*s),
                Point(x=center_x, y=15*s),
                Point(x=center_x + skirt_width*0.2, y=-10*s),
                Point(x=center_x + skirt_width*0.35, y=20*s),
                Point(x=center_x + skirt_width/2, y=0),
            ],
            degree=3,
            layer="Skirt"
        ))

        # Decorative details - ribbon at waist
        entities.splines.append(Spline(
            description="Waist ribbon bow left",
            control_points=[
                Point(x=center_x - waist_width/2, y=waist_y + 10*s),
                Point(x=center_x - waist_width/2 - 60*s, y=waist_y - 30*s),
                Point(x=center_x - waist_width/2 - 80*s, y=waist_y - 80*s),
            ],
            degree=2,
            layer="Details"
        ))

        entities.splines.append(Spline(
            description="Waist ribbon bow right",
            control_points=[
                Point(x=center_x + waist_width/2, y=waist_y + 10*s),
                Point(x=center_x + waist_width/2 + 60*s, y=waist_y - 30*s),
                Point(x=center_x + waist_width/2 + 80*s, y=waist_y - 80*s),
            ],
            degree=2,
            layer="Details"
        ))

        # Fabric folds in skirt (decorative B-splines)
        for i in range(3):
            fold_x = center_x + (i - 1) * skirt_width * 0.2
            entities.splines.append(Spline(
                description=f"Skirt fold {i+1}",
                control_points=[
                    Point(x=fold_x, y=waist_y - 50*s),
                    Point(x=fold_x + 20*s, y=waist_y - skirt_height*0.3),
                    Point(x=fold_x - 10*s, y=waist_y - skirt_height*0.6),
                    Point(x=fold_x + 15*s, y=waist_y - skirt_height*0.85),
                ],
                degree=3,
                layer="Details"
            ))

        entities.notes = f"Princess {style} ball gown silhouette"
        return entities

    def create_from_specifications(self, description: str, specifications: Dict[str, Any]) -> ExtendedEntities:
        """Generate entities from research specifications using LLM.

        This is a fallback method for products not specifically coded.

        Args:
            description: User's description
            specifications: Research data with dimensions and features
        """
        # Build enhanced prompt with specifications
        spec_str = ""
        if specifications:
            dims = specifications.get("dimensions", {})
            features = specifications.get("features", [])
            materials = specifications.get("materials", [])

            if dims:
                spec_str += "\nDimensions:\n"
                for key, value in dims.items():
                    spec_str += f"  - {key}: {value}mm\n"

            if features:
                spec_str += "\nFeatures:\n"
                for feature in features[:10]:
                    spec_str += f"  - {feature}\n"

            if materials:
                spec_str += "\nMaterials: " + ", ".join(materials) + "\n"

        enhanced_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", """Design Request: {description}

Specifications from research:
{specs}

Generate all geometric entities needed for this product.
Use appropriate curve types:
- Lines for straight edges
- Circles for holes and round features
- Arcs for curved edges
- B-Splines for complex smooth profiles
- NURBS for precise curves (corners with exact radii)

All dimensions in millimeters.""")
        ])

        structured_llm = self.llm.with_structured_output(ExtendedEntities)
        chain = enhanced_prompt | structured_llm

        result = chain.invoke({
            "description": description,
            "specs": spec_str if spec_str else "No detailed specifications available. Use reasonable defaults."
        })

        return result

    def extract_advanced(self, user_input: str, intent: Dict[str, Any],
                        research_data: Dict[str, Any] = None) -> ExtendedEntities:
        """Advanced extraction using LLM with full research context.

        Args:
            user_input: User's description
            intent: Parsed intent from IntentParserAgent
            research_data: Optional research results
        """
        # Format research data for prompt
        research_str = ""
        if research_data:
            specs = research_data.get("specifications", {})
            source = research_data.get("source", "unknown")
            confidence = research_data.get("confidence", "medium")

            research_str = f"\n[Research Data - Source: {source}, Confidence: {confidence}]\n"

            dims = specs.get("dimensions", {})
            if dims:
                research_str += "Dimensions:\n"
                for key, value in dims.items():
                    research_str += f"  {key}: {value}mm\n"

            features = specs.get("features", [])
            if features:
                research_str += "Features: " + ", ".join(features[:5]) + "\n"

        # Use enhanced extraction prompt
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", """Design Request: {user_input}

Intent Analysis:
- Drawing Type: {drawing_type}
- Complexity: {complexity}
- Curve Hint: {curve_hint}
- Requirements: {requirements}

{research_data}

Generate complete geometric entities for this design.
Select optimal curve types for each component:
- B-Splines: Smooth organic profiles, fuselages, flowing shapes
- NURBS: Precise circles, ellipses, exact radius corners
- Bezier: Simple decorative curves, transitions
- Polylines with bulge: Efficient mixed straight/curved paths

Ensure mathematical accuracy. All units in mm.""")
        ])

        structured_llm = self.llm.with_structured_output(ExtendedEntities)
        chain = extraction_prompt | structured_llm

        result = chain.invoke({
            "user_input": user_input,
            "drawing_type": intent.get("drawing_type", "general"),
            "complexity": intent.get("complexity_level", "standard"),
            "curve_hint": intent.get("curve_type_hint", "bspline"),
            "requirements": ", ".join(intent.get("requirements", [])),
            "research_data": research_str if research_str else "[No research data available]"
        })

        return result
