"""Entity Extractor Agent - Identifies geometric entities and their parameters."""

from typing import Dict, Any, List, Optional, Union
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class Point(BaseModel):
    """2D Point with x and y coordinates."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")


class Line(BaseModel):
    """Line entity."""
    type: str = Field(default="L", description="Entity type")
    description: str = Field(default="", description="Description of the line")
    x1: float = Field(description="Start X coordinate")
    y1: float = Field(description="Start Y coordinate")
    x2: float = Field(description="End X coordinate")
    y2: float = Field(description="End Y coordinate")
    layer: str = Field(default="0", description="Layer name")


class Circle(BaseModel):
    """Circle entity."""
    type: str = Field(default="C", description="Entity type")
    description: str = Field(default="", description="Description of the circle")
    center_x: float = Field(description="Center X coordinate")
    center_y: float = Field(description="Center Y coordinate")
    radius: float = Field(description="Radius")
    layer: str = Field(default="0", description="Layer name")


class Arc(BaseModel):
    """Arc entity."""
    type: str = Field(default="A", description="Entity type")
    description: str = Field(default="", description="Description of the arc")
    center_x: float = Field(description="Center X coordinate")
    center_y: float = Field(description="Center Y coordinate")
    radius: float = Field(description="Radius")
    start_angle: float = Field(description="Start angle in degrees")
    end_angle: float = Field(description="End angle in degrees")
    layer: str = Field(default="0", description="Layer name")


class Polyline(BaseModel):
    """Polyline entity."""
    type: str = Field(default="P", description="Entity type")
    description: str = Field(default="", description="Description of the polyline")
    points: List[Point] = Field(description="List of (x, y) coordinate points")
    closed: bool = Field(default=False, description="Whether the polyline is closed")
    layer: str = Field(default="0", description="Layer name")


class Hatch(BaseModel):
    """Hatch entity."""
    type: str = Field(default="H", description="Entity type")
    description: str = Field(default="", description="Description of the hatch")
    boundary_points: List[Point] = Field(description="Boundary points for the hatch")
    pattern: str = Field(default="SOLID", description="Hatch pattern")
    layer: str = Field(default="0", description="Layer name")


class ExtractedEntities(BaseModel):
    """Collection of extracted entities."""

    lines: List[Line] = Field(default_factory=list, description="List of line entities")
    circles: List[Circle] = Field(default_factory=list, description="List of circle entities")
    arcs: List[Arc] = Field(default_factory=list, description="List of arc entities")
    polylines: List[Polyline] = Field(default_factory=list, description="List of polyline entities")
    hatches: List[Hatch] = Field(default_factory=list, description="List of hatch entities")
    notes: str = Field(default="", description="Additional notes or clarifications needed")


class EntityExtractorAgent:
    """Agent that extracts specific geometric entities from drawing intent."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting geometric entities from natural language drawing descriptions. Your job is to semantically understand ANY description - from architectural blueprints to mechanical parts to furniture - and translate it into precise geometric entities.

**Available Entity Types:**
- **Lines (L)**: x1, y1, x2, y2 coordinates (for walls, edges, pipes, structural elements)
- **Circles (C)**: center_x, center_y, radius (for wheels, gears, pipes, circular features)
- **Arcs (A)**: center_x, center_y, radius, start_angle, end_angle in degrees (for curved elements, door swings)
- **Polylines (P)**: list of (x, y) points, closed flag (for rooms, furniture outlines, complex shapes)
- **Hatches (H)**: boundary points, pattern type (for filled areas, floor materials, cross-sections)

**Semantic Understanding Process:**

1. **Interpret What's Being Described**:
   Understand the domain and what geometric primitives make sense:

   *Architectural/Blueprint elements:*
   - "room/chamber" → closed polyline (rectangle) with walls as lines
   - "door" → THREE elements required:
     1. Hinge line (25mm): short line perpendicular to wall at hinge
     2. Door leaf line: line from hinge showing door panel (door_width - 25mm long)
     3. Swing arc: 90° arc with radius = door_width - 25mm, center at end of hinge line
     Example: 900mm door → 25mm hinge line + 875mm door leaf + 875mm radius arc
   - "window" → lines with small perpendicular marks
   - "wall" → lines (or double lines for thickness)
   - "warehouse" → large rectangular spaces with loading docks, columns

   *Mechanical/Technical parts:*
   - "gear" → circle with teeth (small rectangles or lines radiating outward)
   - "pipe/plumbing" → circles (cross-section) or parallel lines (side view)
   - "valve" → combination of circles and lines
   - "bolt/screw" → circle with cross lines or hexagon (closed polyline)

   *Furniture/Appliances:*
   - "chair" → rectangles/polylines for seat and back, lines for legs
   - "table" → rectangle/circle for top, lines for legs
   - "TV" → rectangle with smaller inner rectangle for screen
   - "sofa/couch" → larger rectangles with cushion divisions
   - "bed" → rectangle with smaller rectangle for pillow area

2. **Understand Spatial Language**:
   - "scattered", "centered", "around", "at each corner/quarter", "patterned", "concentric", "adjacent", "opposite"
   - "outward facing", "inward", "pointing to", "aligned with"
   - Directional: "north wall", "left side", "top-right corner"

3. **Interpret Dimensional Descriptions**:
   - Explicit: "3 by 3", "100x50", "5mm", "10 feet"
   - Implicit: "3 by 3" or "3x3" means a rectangle with width 3 and height 3
   - Relative: "small", "large", "twice as big", "standard door size (900x2100mm)"
   - Contextual: understand typical sizes (e.g., rooms are meters, gears are mm)

4. **Calculate Positions and Relationships**:
   - Use trigonometry for angular positioning: x = center_x + radius*cos(angle_rad), y = center_y + radius*sin(angle_rad)
   - For "scattered": distribute randomly but evenly within bounds
   - For "patterned/grid": use regular intervals
   - For "outward facing door": arc opens away from room center
   - Consider spatial relationships: doors in walls, furniture against walls, etc.

5. **Assign Layers and Descriptions**:
   - Use meaningful layer names: "Walls", "Doors", "Furniture", "Plumbing", "Electrical", "Dimensions"
   - Provide clear descriptions for traceability

**Professional Standards Database** (CRITICAL - Apply These Standards):

*Architectural:*
- Wall thickness: 150mm (interior), 200mm (exterior)
- Door dimensions: 900mm wide (interior), 1000mm (exterior), 800mm (bathroom), all 2100mm height
- Door panel thickness: 25mm (for plan view representation)
- Door arc radius = door_width - 25mm (e.g., 900mm door → 875mm arc radius)
- Window dimensions: 1200×1200mm (standard), 1800×1200mm (large)
- Room minimums: Bedroom 3000×3000mm, Living 4000×5000mm, Bathroom 2000×2000mm, Kitchen 3000×3000mm
- Hallway width: 1200mm minimum
- Ceiling height: 2700mm (residential), 3000mm (commercial)

*Furniture Placement:*
- Position furniture on proportional grid: 1/2, 1/4, 1/8, or 1/16 of room dimensions
- Example: 5000mm room → valid positions: 2500, 1250, 625, 312.5mm from walls
- Maintain clearances: 600mm around beds, 900mm for desk/chair, 750mm passages
- Align furniture parallel to walls (0° or 90° only)

*Mechanical:*
- Gear module: 1, 1.5, 2, 2.5, 3, 4, 5mm (common sizes)
- Gear teeth: 12-120 typical range
- Bearing sizes: ID 6-100mm, OD ~2.5× ID
- Bolt sizes: M3, M4, M5, M6, M8, M10, M12 (metric standard)
- Shaft diameters: 6, 8, 10, 12, 15, 20, 25, 30, 40, 50mm (preferred sizes)

*Furniture:*
- Single bed: 1000×2000mm, Double: 1400×2000mm, King: 2000×2000mm
- Dining table 6p: 1800×900mm, Coffee table: 1200×600mm
- Sofa 3-seat: 2000×900mm, Desk: 1400×700mm
- Chair seat height: 450mm, Table height: 750mm

**Key Principles**:
- Think semantically: understand MEANING and INTENT, not just keywords
- Be domain-aware: architectural drawings vs mechanical parts have different conventions
- Be creative and logical: translate abstract concepts into concrete geometry
- Infer intelligently: use context, typical standards, and spatial reasoning
- Be complete: generate all entities needed to represent the described structure
- **ALWAYS apply professional standards** when dimensions are not specified

**Example Interpretations (Diverse Contexts):**

*Architectural & Buildings:*
- "house plan with 3 rooms and outward facing doors" → 3 closed polylines (rooms), gaps in walls, arcs showing door swing outward
- "office layout with cubicles in a grid" → grid of rectangular polylines, lines for desks/partitions
- "cathedral floor plan with nave and transept" → cross-shaped layout using polylines, circles for columns
- "parking lot with 20 angled spaces" → parallel angled rectangles in rows
- "theater with curved seating rows" → concentric arcs/polylines facing a stage rectangle
- "spiral staircase" → series of arcs or circles with decreasing radius, connected by lines

*Mechanical & Engineering:*
- "gear with 8 teeth" → circle + 8 small rectangles radially positioned
- "pulley system with 3 wheels" → multiple circles connected by lines (belt path)
- "chain link pattern" → interlocking circles or ovals in a line
- "spring coil" → spiral of connected arcs
- "bolt with hexagonal head" → hexagon (6-point polyline) + circle for shaft
- "bearing assembly" → concentric circles with lines for mounting holes

*Plumbing & HVAC:*
- "plumbing layout with pipes and valves" → parallel lines (pipes), circles (joints), symbols for valves
- "T-junction with 3 pipes" → three lines meeting at right angles
- "ductwork with 90-degree elbow" → rectangles connected at right angle
- "water heater with inlet/outlet" → rectangle/circle with two small circles for connections

*Furniture & Interior:*
- "L-shaped couch in corner" → L-shaped polyline with cushion divisions
- "dining table with 6 chairs" → rectangle/circle (table) + 6 smaller rectangles around it (chairs)
- "desk with drawers" → rectangle with internal lines showing drawer divisions
- "bookshelf with 5 shelves" → rectangle with horizontal lines
- "king size bed" → large rectangle (approx 2000x1800mm) with pillow area

*Electronics & Appliances:*
- "TV with stand" → large rectangle (screen) + smaller rectangle below (stand)
- "refrigerator with freezer on top" → rectangle divided horizontally
- "washing machine" → circle (drum view) or rectangle (front view) with circle inside
- "microwave" → rectangle with smaller inner rectangle (window) and circle (turntable)
- "ceiling fan with 4 blades" → circle (motor) + 4 lines radiating out at 90° intervals

*Garden & Landscape:*
- "garden with circular fountain in center and flower beds at corners" → central circle, 4 curved polylines at corners
- "patio with pergola" → rectangle (patio) with parallel lines (pergola beams)
- "driveway with curved path" → connected arcs and lines showing path
- "swimming pool with steps" → organic polyline shape with rectangular step area

*Industrial & Warehouse:*
- "warehouse with loading dock and office" → large rectangle (main space), smaller rectangle (office), indented area (dock)
- "factory floor with assembly line" → long rectangle with circles/rectangles (stations) along a line
- "storage rack layout" → grid of rectangles showing shelving units

*Abstract & Creative:*
- "roller coaster style staircase" → wavy pattern of connected arcs and lines with step-like segments
- "mandala pattern" → concentric circles with radial lines and repeated geometric shapes
- "maze layout" → network of connected lines forming paths and dead ends
- "fractal tree" → branching lines with decreasing length at each level
- "honeycomb pattern" → tessellated hexagons (6-point polylines)

*Sports & Recreation:*
- "basketball court" → rectangle with circle (center), arcs (3-point lines), smaller rectangles (key)
- "tennis court" → rectangle with internal lines (service boxes, center)
- "running track oval" → two parallel lines connected by semicircular arcs

*Urban Planning:*
- "city block with buildings and roads" → grid of rectangles (buildings) with lines (roads) between them
- "roundabout with 4 exits" → circle with 4 lines radiating out
- "intersection with crosswalks" → perpendicular lines with parallel lines (crosswalk stripes)

*Medical & Laboratory:*
- "hospital room with bed and equipment" → rectangle (room) with smaller rectangles (bed, equipment)
- "lab bench with sinks" → long rectangle with circles (sinks) positioned along it

*Military & Defense:*
- "castle with moat and towers at corners" → concentric circles/rectangles, circles at corners (towers)
- "fortification with star-shaped walls" → star-shaped polyline with outward-pointing triangular bastions

Remember: These are guides, not rigid rules. Use semantic understanding to interpret ANY description creatively and logically.

If critical information cannot be reasonably inferred, note it in the 'notes' field."""),
            ("user", "Drawing Intent:\n{intent}\n\nUser Description:\n{user_input}")
        ])

    def extract(self, user_input: str, intent: Dict[str, Any]) -> ExtractedEntities:
        """Extract geometric entities from user input and parsed intent."""
        structured_llm = self.llm.with_structured_output(ExtractedEntities)
        chain = self.prompt | structured_llm
        result = chain.invoke({
            "user_input": user_input,
            "intent": str(intent)
        })
        return result
