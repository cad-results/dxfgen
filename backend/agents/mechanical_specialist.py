"""Mechanical Parts Specialist Agent - Engineering-grade mechanical part generation."""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .entity_extractor import ExtractedEntities, Line, Circle, Arc, Polyline, Point
import math


class MechanicalSpecialistAgent:
    """
    Specialized agent for generating engineering-grade mechanical parts and assemblies.

    Generates technical drawings for:
    - Gears (spur, helical) with proper tooth geometry
    - Bearings and bushings
    - Fasteners (bolts, screws, nuts)
    - Shafts and couplings
    - Pulleys and sprockets
    - Custom machine parts
    - With engineering annotations and tolerances
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert mechanical engineer and technical draftsman specializing in precision machine part design for CAD/DXF output.

**Your Mission**: Generate ENGINEERING-GRADE technical drawings of mechanical parts with proper dimensions, tolerances, and manufacturing considerations.

**Engineering Standards:**

1. **Gear Standards** (Spur Gears):
   - Module (m): tooth size parameter (1, 1.5, 2, 2.5, 3, 4, 5mm typical)
   - Number of teeth (z): 12-120 typical
   - Pitch diameter (d): d = m × z
   - Outer diameter (da): da = m × (z + 2)
   - Root diameter (df): df = m × (z - 2.5)
   - Pressure angle: 20° (standard) or 14.5° (older standard)
   - Tooth spacing: 360° / z
   - Tooth height: 2.25 × module
   - Addendum: 1.0 × module
   - Dedendum: 1.25 × module

   **Gear Tooth Representation** (simplified for 2D DXF):
   - Base circle (pitch diameter)
   - Outer circle (outer diameter)
   - Root circle (root diameter)
   - Tooth profiles: small trapezoids or triangles radiating outward

2. **Bearing Standards**:
   - Deep groove ball bearing: inner circle (bore), outer circle (OD), ball centers circle
   - Inner diameter: shaft size (6, 8, 10, 12, 15, 17, 20, 25mm typical)
   - Outer diameter: ~2.5-3× inner diameter
   - Width: ~0.3-0.6× outer diameter
   - Representation: concentric circles with cross-section view

3. **Fastener Standards** (ISO Metric):
   - M3: 3mm nominal diameter, 5.5mm head, 2.5mm head height
   - M4: 4mm diameter, 7mm head, 3mm head height
   - M5: 5mm diameter, 8mm head, 3.5mm head height
   - M6: 6mm diameter, 10mm head, 4mm head height
   - M8: 8mm diameter, 13mm head, 5.5mm head height
   - M10: 10mm diameter, 17mm head, 7mm head height
   - M12: 12mm diameter, 19mm head, 8mm head height
   - Hex head: regular hexagon (6-point polyline)
   - Thread representation: parallel lines on shaft

4. **Shaft Standards**:
   - Diameter: based on torque requirements (6-100mm typical)
   - Length: varies by application
   - Keyway: rectangular slot for key (width = diameter/4 typical)
   - Shoulder: step diameter for bearing seating
   - Chamfer: 0.5-2mm × 45° at ends
   - Representation: rectangle (side view) with center lines

5. **Pulley/Sprocket Standards**:
   - Pulley diameter: based on speed ratio
   - Rim thickness: 5-10mm
   - Web thickness: 3-8mm
   - Hub bore: shaft diameter + tolerance
   - V-belt pulleys: groove angle 40°, depth based on belt size
   - Chain sprockets: teeth match chain pitch

6. **Layer Organization**:
   - "Outlines" layer: Main part outlines
   - "CenterLines" layer: Center lines, axis lines
   - "Dimensions" layer: Dimension lines and text
   - "Tolerances" layer: Tolerance callouts
   - "Threads" layer: Thread representations
   - "Hidden" layer: Hidden lines (dashed)
   - "Hatching" layer: Cross-section hatching

7. **Machining Analysis**:
   - Tolerances: H7/g6 for shaft/hole fits (typical)
   - Surface finish: Ra 0.8-3.2 μm for bearing surfaces
   - Material considerations: steel (most common), aluminum, bronze
   - Machining feasibility: avoid sharp internal corners, provide tool access
   - Minimum wall thickness: 3mm (aluminum), 2mm (steel)

8. **Engineering Drawing Conventions**:
   - Center lines: dash-dot pattern (represent with regular lines + description)
   - Hidden lines: dashed (represent with regular lines + description on "Hidden" layer)
   - Dimension lines: with arrows and text
   - Use standard views: front, side, section as needed
   - Include critical dimensions only

**Common Mechanical Parts Library:**

**Spur Gear (example: 20 teeth, module 2)**:
- Pitch diameter: 40mm
- Outer diameter: 44mm
- Root diameter: 35mm
- Generate: 3 concentric circles + 20 tooth profiles

**Ball Bearing (example: 6205)**:
- Inner diameter: 25mm
- Outer diameter: 52mm
- Width: 15mm
- Generate: 2 concentric circles (section view)

**Hex Bolt M8×40**:
- Shank diameter: 8mm (circle)
- Head: 13mm hex (6-point polyline)
- Length: 40mm
- Thread: simplified as parallel lines

**Shaft with Keyway**:
- Diameter: 20mm
- Length: 100mm
- Keyway: 5mm wide × 5mm deep
- Generate: rectangle (side view) with keyway slot

**Workflow:**

1. Parse specification:
   - Identify part type (gear, bearing, shaft, fastener, etc.)
   - Extract key parameters (size, count, arrangement)
   - Determine view type (plan, elevation, section)

2. Calculate geometry:
   - Apply engineering formulas
   - Calculate all critical dimensions
   - Verify manufacturability

3. Generate entities:
   - Main outlines (circles, lines, polylines)
   - Detail features (teeth, threads, keyways)
   - Center lines and construction geometry
   - Dimension lines (if annotations enabled)

4. Apply layers:
   - Organize by feature type
   - Use engineering layer conventions

5. Add engineering notes:
   - Critical dimensions
   - Tolerance callouts
   - Material specifications

**Example: 24-Tooth Spur Gear, Module 2.5**

Calculations:
- Pitch diameter: 2.5 × 24 = 60mm
- Outer diameter: 2.5 × (24 + 2) = 65mm
- Root diameter: 2.5 × (24 - 2.5) = 53.75mm
- Tooth angle: 360 / 24 = 15° spacing

Entities to generate:
- Circle (pitch diameter 60mm) on "Outlines"
- Circle (outer diameter 65mm) on "Outlines"
- Circle (root diameter 53.75mm) on "Outlines"
- 24 tooth profiles (small trapezoids) radially spaced 15° apart
- Circle (bore 20mm typical) on "Outlines"
- Center lines (vertical + horizontal) on "CenterLines"

Be precise, engineering-accurate, and thorough."""),
            ("user", """Refined Specification:
{refined_specification}

User Settings:
- Include annotations: {include_annotations}
- Quality level: {quality_level}

Please generate complete, engineering-grade mechanical part entities.""")
        ])

    def generate_mechanical_part(
        self,
        refined_specification: str,
        include_annotations: bool = True,
        quality_level: str = "professional"
    ) -> ExtractedEntities:
        """Generate mechanical part entities."""
        structured_llm = self.llm.with_structured_output(ExtractedEntities)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "refined_specification": refined_specification,
            "include_annotations": include_annotations,
            "quality_level": quality_level
        })

        return result

    @staticmethod
    def create_spur_gear(
        center_x: float,
        center_y: float,
        module: float,
        num_teeth: int,
        bore_diameter: float = 0.0,
        layer: str = "Outlines"
    ) -> List[Any]:  # Returns List[Circle | Line | Polyline]
        """
        Create a simplified spur gear representation.

        Args:
            center_x, center_y: Gear center
            module: Gear module (tooth size)
            num_teeth: Number of teeth
            bore_diameter: Center bore diameter (0 for no bore)
            layer: Layer name

        Returns:
            List of entities representing the gear
        """
        entities = []

        # Calculate dimensions
        pitch_diameter = module * num_teeth
        outer_diameter = module * (num_teeth + 2)
        root_diameter = module * (num_teeth - 2.5)

        # Main circles
        entities.append(Circle(
            center_x=center_x,
            center_y=center_y,
            radius=outer_diameter / 2,
            description=f"Gear outer circle (OD={outer_diameter:.1f}mm)",
            layer=layer
        ))

        entities.append(Circle(
            center_x=center_x,
            center_y=center_y,
            radius=pitch_diameter / 2,
            description=f"Gear pitch circle (PD={pitch_diameter:.1f}mm)",
            layer=layer
        ))

        entities.append(Circle(
            center_x=center_x,
            center_y=center_y,
            radius=root_diameter / 2,
            description=f"Gear root circle (RD={root_diameter:.1f}mm)",
            layer=layer
        ))

        # Bore
        if bore_diameter > 0:
            entities.append(Circle(
                center_x=center_x,
                center_y=center_y,
                radius=bore_diameter / 2,
                description=f"Gear bore (D={bore_diameter:.1f}mm)",
                layer=layer
            ))

        # Simplified tooth representation (radial lines)
        tooth_angle = 360.0 / num_teeth
        for i in range(num_teeth):
            angle_deg = i * tooth_angle
            angle_rad = math.radians(angle_deg)

            # Radial line from root to outer circle
            x_start = center_x + (root_diameter / 2) * math.cos(angle_rad)
            y_start = center_y + (root_diameter / 2) * math.sin(angle_rad)
            x_end = center_x + (outer_diameter / 2) * math.cos(angle_rad)
            y_end = center_y + (outer_diameter / 2) * math.sin(angle_rad)

            entities.append(Line(
                x1=x_start,
                y1=y_start,
                x2=x_end,
                y2=y_end,
                description=f"Gear tooth {i+1}",
                layer=layer
            ))

        return entities

    @staticmethod
    def create_bearing(
        center_x: float,
        center_y: float,
        bore_diameter: float,
        outer_diameter: float,
        layer: str = "Outlines"
    ) -> List[Circle]:
        """
        Create a ball bearing representation (section view).

        Args:
            center_x, center_y: Bearing center
            bore_diameter: Inner diameter
            outer_diameter: Outer diameter
            layer: Layer name

        Returns:
            List of Circle entities
        """
        entities = []

        # Outer circle
        entities.append(Circle(
            center_x=center_x,
            center_y=center_y,
            radius=outer_diameter / 2,
            description=f"Bearing outer race (OD={outer_diameter:.1f}mm)",
            layer=layer
        ))

        # Inner circle
        entities.append(Circle(
            center_x=center_x,
            center_y=center_y,
            radius=bore_diameter / 2,
            description=f"Bearing inner race (ID={bore_diameter:.1f}mm)",
            layer=layer
        ))

        # Ball pitch circle (midpoint)
        ball_pitch = (outer_diameter + bore_diameter) / 4
        entities.append(Circle(
            center_x=center_x,
            center_y=center_y,
            radius=ball_pitch,
            description="Bearing ball pitch circle",
            layer=layer
        ))

        return entities

    @staticmethod
    def create_hex_bolt(
        x: float,
        y: float,
        diameter: float,
        length: float,
        layer: str = "Outlines"
    ) -> List[Any]:  # Returns List[Circle | Polyline]
        """
        Create a hex bolt representation (side view).

        Args:
            x, y: Bolt center position
            diameter: Nominal diameter (M6, M8, etc.)
            length: Total length including head
            layer: Layer name

        Returns:
            List of entities
        """
        entities = []

        # Head dimensions (simplified)
        head_width = diameter * 1.6  # Approximate across-flats
        head_height = diameter * 0.7

        # Hex head (6-point polyline)
        hex_points = []
        for i in range(6):
            angle = math.radians(60 * i)
            px = x + (head_width / 2) * math.cos(angle)
            py = y + (head_width / 2) * math.sin(angle)
            hex_points.append(Point(x=px, y=py))

        entities.append(Polyline(
            points=hex_points,
            closed=True,
            description=f"Bolt head M{diameter:.0f}",
            layer=layer
        ))

        # Shank (circle for top view, or rectangle for side view)
        # Using top view (circle)
        entities.append(Circle(
            center_x=x,
            center_y=y - head_height - length/2,
            radius=diameter / 2,
            description=f"Bolt shank M{diameter:.0f}×{length:.0f}",
            layer=layer
        ))

        return entities
