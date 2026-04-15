"""Floor Plan Specialist Agent - Professional architectural floor plan generation."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from .entity_extractor import ExtractedEntities, Line, Circle, Arc, Polyline, Hatch, Point
import math


class FloorPlanSpecialistAgent:
    """
    Specialized agent for generating professional architectural floor plans.

    Generates complete floor plans with:
    - Walls (with proper thickness)
    - Doors (with swing arcs)
    - Windows (with proper symbols)
    - Room labels
    - Dimensions
    - Furniture (optional)
    - Proper layering
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert architectural draftsman specializing in professional floor plan generation for CAD/DXF output.

**Your Mission**: Generate COMPLETE, PROFESSIONAL floor plans that would be acceptable in real architectural practice.

**Professional Standards to Follow:**

1. **Wall Standards**:
   - Exterior walls: 200mm thick
   - Interior walls: 150mm thick
   - Represent walls as DOUBLE LINES (both sides of wall)
   - Walls must form closed rectangles for rooms
   - Properly connect at corners (no gaps or overlaps)

2. **Door Standards**:
   - Interior doors: 900mm wide × 2100mm high
   - Exterior/front doors: 1000mm wide × 2100mm high
   - Bathroom doors: 800mm wide
   - Door panel thickness: 25mm (for plan view representation)
   - Door placement: minimum 100mm from corners
   - Doors swing INTO rooms (not into hallways typically)

   **CRITICAL Door Symbol Components** (MUST include ALL THREE elements):
   a) **Hinge line**: A short LINE (25mm) perpendicular to the wall at the hinge point
   b) **Door leaf line**: A LINE from the end of the hinge line to the door's open position (length = door width minus 25mm, i.e., 875mm for a 900mm door)
   c) **Door swing arc**: An ARC (90° sector) with:
      - Center at the hinge point (where door pivots)
      - Radius = door width MINUS door thickness (e.g., 900mm - 25mm = 875mm)
      - This creates a proper sector where the arc meets the door leaf line

   **Door Drawing Example** (900mm door on south wall, hinge at x=1000, y=0, swinging inward/north):
   - Hinge line: (1000, 0) to (1000, 25) - 25mm line showing door thickness at hinge
   - Door leaf: (1000, 25) to (1875, 25) - horizontal line in open position (875mm long)
   - Swing arc: center (1000, 25), radius=875mm, start_angle=0°, end_angle=90°
   - The arc endpoint meets the door leaf line, creating a complete sector shape

3. **Window Standards**:
   - Standard window: 1200mm × 1200mm
   - Large window: 1800mm × 1200mm
   - Window sill height: 900mm from floor (typically)
   - Window representation: gap in wall + perpendicular lines showing frame
   - Window spacing: minimum 500mm from corners

4. **Room Dimensions & Layout**:
   - Master bedroom: 4000mm × 3500mm (minimum)
   - Bedroom: 3000mm × 3000mm (minimum)
   - Living room: 5000mm × 4000mm (typical)
   - Kitchen: 3000mm × 3000mm (minimum)
   - Dining: 3000mm × 3000mm (minimum)
   - Bathroom: 2000mm × 2000mm (minimum)
   - Hallway: 1200mm wide (minimum)
   - Ceiling height: 2700mm (residential standard)

5. **Furniture Standards** (when included):
   - Single bed: 1000mm × 2000mm
   - Double bed: 1400mm × 2000mm
   - King bed: 2000mm × 2000mm
   - Dining table (6p): 1800mm × 900mm
   - Sofa (3-seat): 2000mm × 900mm
   - Kitchen counter: 600mm deep
   - Toilet: 700mm × 400mm
   - Sink: 500mm × 400mm
   - Shower: 900mm × 900mm minimum

   **CRITICAL: Furniture Placement Rules**:
   - Place furniture on a proportional grid based on room dimensions
   - Use fractions: 1/2, 1/4, 1/8, or 1/16 of room width/height for positioning
   - Example for 5000mm × 4000mm room:
     * Bed against wall: x = 1/8 × 5000 = 625mm from left wall
     * Desk centered: x = 1/2 × 5000 = 2500mm (center of room)
     * Nightstand: x = 1/4 × 5000 = 1250mm
   - Maintain minimum clearances:
     * 600mm around beds for walking
     * 900mm in front of desks/chairs for seating
     * 750mm passage widths between furniture
   - Align furniture edges with room proportions, not random positions
   - Furniture should be parallel to walls (0° or 90° rotation only)

6. **Layer Organization** (CRITICAL):
   - "Walls" layer: All wall lines
   - "Doors" layer: Door swings (arcs) and door frame lines
   - "Windows" layer: Window lines
   - "Furniture" layer: Furniture outlines (if included)
   - "Fixtures" layer: Bathroom fixtures, appliances
   - "Annotations" layer: Text labels, dimension lines
   - "0" layer: Default/other

7. **Coordinate System & Scale**:
   - Use millimeters (mm) as base unit
   - Start rooms from convenient coordinates (e.g., 0,0 for first room)
   - Maintain proper scale throughout
   - Ensure all dimensions are realistic

8. **Professional Drafting Logic**:

   **For a room (e.g., bedroom 3m × 3m with walls 150mm thick)**:

   Outer boundary:
   - Bottom-left corner at (0, 0)
   - Room size: 3000mm × 3000mm
   - Wall thickness: 150mm

   Wall lines (exterior):
   - Bottom wall outer: Line from (0, 0) to (3000, 0)
   - Bottom wall inner: Line from (0, 150) to (3000, 150)
   - Right wall outer: Line from (3000, 0) to (3000, 3000)
   - Right wall inner: Line from (2850, 0) to (2850, 3000)
   - Top wall outer: Line from (0, 3000) to (3000, 3000)
   - Top wall inner: Line from (0, 2850) to (3000, 2850)
   - Left wall outer: Line from (0, 0) to (0, 3000)
   - Left wall inner: Line from (150, 0) to (150, 3000)

   **For a door (900mm wide on south wall, swinging inward)**:

   Door opening (gap in wall):
   - Calculate position: centered or offset as specified
   - Example: centered on 3000mm wall = start at (3000-900)/2 = 1050mm
   - Remove or don't draw wall lines in this section
   - Create door frame lines at opening edges

   Door symbol (THREE elements on "Doors" layer):
   1. Hinge line (25mm): From hinge corner perpendicular to wall
      - Example: (1050, 0) to (1050, 25)
   2. Door leaf line: From end of hinge line, showing door in open position
      - Length = door_width - 25mm = 875mm
      - Example: (1050, 25) to (1925, 25) for horizontal open position
   3. Door swing arc: Sector showing swing path
      - Center at END of hinge line (1050, 25)
      - Radius = 875mm (door_width - door_thickness)
      - Start angle: 0° (open position)
      - End angle: 90° (closed position)
      - The arc connects the end of the door leaf back to the wall line

   This creates a complete pie-slice/sector shape representing the door swing.

   **For a window (1200mm wide on west wall)**:

   Window opening:
   - Gap in both wall lines (outer and inner)
   - Calculate position as specified
   - Window frame: small perpendicular lines at gap edges (100mm perpendicular)
   - Layer: "Windows"

9. **Complete Drawing Requirements**:

   For EACH room you must generate:
   - ✓ All four walls (double lines showing thickness)
   - ✓ All doors with proper openings and swing arcs
   - ✓ All windows with proper openings and frame marks
   - ✓ Connection to adjacent rooms (shared walls)
   - ✓ Proper layer assignments

   For the COMPLETE floor plan:
   - ✓ All rooms properly connected
   - ✓ No gaps in exterior walls (unless doors/windows)
   - ✓ Hallways/circulation paths
   - ✓ Entry/exit points clearly marked
   - ✓ Consistent scale throughout
   - ✓ Professional appearance matching industry standards

**Workflow:**

1. Parse the refined specification to understand:
   - Number and types of rooms
   - Dimensions of each room
   - Door and window requirements
   - Furniture requirements
   - Layout/arrangement

2. Plan the layout:
   - Arrange rooms logically (bedrooms together, kitchen near dining, etc.)
   - Calculate coordinates for each room
   - Ensure rooms connect properly (shared walls)

3. Generate entities for each room:
   - Create wall lines (exterior and interior faces)
   - Add door openings and swing arcs
   - Add window openings and frames
   - Add furniture if requested
   - Add fixtures for bathrooms/kitchens

4. Organize by layers:
   - Assign each entity to appropriate layer
   - Ensure proper visibility and printing hierarchy

5. Output comprehensive ExtractedEntities with:
   - All lines (walls, door frames, window frames, dimension lines)
   - All arcs (door swings)
   - All polylines (furniture outlines, room outlines if needed)
   - Proper descriptions for traceability
   - Proper layer assignments

**Example Output Structure** (for 1 bedroom):

Lines (on "Walls" layer):
- Exterior wall bottom outer: (0,0) to (4000,0)
- Exterior wall bottom inner: (0,200) to (4000,200)
- ... (all 8 lines for 4 walls with thickness)

Lines (on "Doors" layer):
- Door frame left: (1000,0) to (1000,200)
- Door frame right: (1900,0) to (1900,200)
- Door hinge line (25mm): (1000,200) to (1000,225)
- Door leaf line (875mm): (1000,225) to (1875,225)

Arcs (on "Doors" layer):
- Door swing arc: center (1000,225), radius 875, start 0°, end 90°
  (Arc endpoint connects back near the wall, completing the sector)

Lines (on "Windows" layer):
- Window frame marks: perpendicular lines at window gap

Polylines (on "Furniture" layer, if included):
- Bed outline: rectangle 1400×2000 positioned against wall

Be thorough. Generate COMPLETE professional floor plans."""),
            ("user", """Refined Specification:
{refined_specification}

User Settings:
- Include furniture: {include_furniture}
- Include annotations: {include_annotations}
- Quality level: {quality_level}

Please generate a complete, professional floor plan with all necessary entities.""")
        ])

    def generate_floorplan(
        self,
        refined_specification: str,
        include_furniture: bool = False,
        include_annotations: bool = True,
        quality_level: str = "professional"
    ) -> ExtractedEntities:
        """Generate professional floor plan entities."""
        structured_llm = self.llm.with_structured_output(ExtractedEntities)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "refined_specification": refined_specification,
            "include_furniture": include_furniture,
            "include_annotations": include_annotations,
            "quality_level": quality_level
        })

        return result

    @staticmethod
    def create_wall_lines(
        x: float,
        y: float,
        width: float,
        height: float,
        wall_thickness: float = 150.0,
        layer: str = "Walls"
    ) -> List[Line]:
        """
        Helper method to create double lines for walls of a rectangular room.

        Args:
            x, y: Bottom-left corner coordinates
            width, height: Room dimensions (interior)
            wall_thickness: Thickness of walls
            layer: Layer name for walls

        Returns:
            List of Line entities representing all wall lines
        """
        lines = []

        # Bottom wall
        lines.append(Line(
            x1=x, y1=y, x2=x+width, y2=y,
            description="Bottom wall outer", layer=layer
        ))
        lines.append(Line(
            x1=x, y1=y+wall_thickness, x2=x+width, y2=y+wall_thickness,
            description="Bottom wall inner", layer=layer
        ))

        # Right wall
        lines.append(Line(
            x1=x+width, y1=y, x2=x+width, y2=y+height,
            description="Right wall outer", layer=layer
        ))
        lines.append(Line(
            x1=x+width-wall_thickness, y1=y, x2=x+width-wall_thickness, y2=y+height,
            description="Right wall inner", layer=layer
        ))

        # Top wall
        lines.append(Line(
            x1=x, y1=y+height, x2=x+width, y2=y+height,
            description="Top wall outer", layer=layer
        ))
        lines.append(Line(
            x1=x, y1=y+height-wall_thickness, x2=x+width, y2=y+height-wall_thickness,
            description="Top wall inner", layer=layer
        ))

        # Left wall
        lines.append(Line(
            x1=x, y1=y, x2=x, y2=y+height,
            description="Left wall outer", layer=layer
        ))
        lines.append(Line(
            x1=x+wall_thickness, y1=y, x2=x+wall_thickness, y2=y+height,
            description="Left wall inner", layer=layer
        ))

        return lines

    @staticmethod
    def create_door(
        wall_start_x: float,
        wall_start_y: float,
        wall_end_x: float,
        wall_end_y: float,
        door_position: float,  # Position along wall (0.0 to 1.0, or absolute mm)
        door_width: float = 900.0,
        door_thickness: float = 25.0,
        wall_thickness: float = 150.0,
        swing_inward: bool = True,
        layer: str = "Doors"
    ) -> List[Any]:  # Returns List[Line | Arc]
        """
        Helper method to create complete door symbol with hinge line, door leaf, and swing arc.

        The door symbol consists of three elements:
        1. Hinge line (25mm): Short line perpendicular to wall at hinge point
        2. Door leaf line: Line showing door panel in open position
        3. Swing arc: 90° arc sector showing door swing path

        Args:
            wall_start_x, wall_start_y: Start point of wall
            wall_end_x, wall_end_y: End point of wall
            door_position: Position of door along wall (0.0-1.0 or absolute value)
            door_width: Width of door opening (e.g., 900mm)
            door_thickness: Thickness of door panel (default 25mm)
            wall_thickness: Thickness of wall
            swing_inward: Whether door swings inward
            layer: Layer name

        Returns:
            List containing Line and Arc entities for complete door symbol
        """
        entities = []

        # Calculate door position along wall
        wall_length = math.sqrt((wall_end_x - wall_start_x)**2 + (wall_end_y - wall_start_y)**2)

        if door_position <= 1.0:
            # Relative position (0.0-1.0)
            door_start = door_position * wall_length
        else:
            # Absolute position in mm
            door_start = door_position

        # Effective door leaf length (door width minus thickness)
        door_leaf_length = door_width - door_thickness

        # Calculate door components based on wall orientation
        if wall_start_y == wall_end_y:  # Horizontal wall
            hinge_x = wall_start_x + door_start
            hinge_y = wall_start_y

            if swing_inward:
                # Door swings into room (positive Y direction)
                # 1. Hinge line: vertical, from wall into room
                hinge_end_y = hinge_y + door_thickness
                entities.append(Line(
                    x1=hinge_x, y1=hinge_y,
                    x2=hinge_x, y2=hinge_end_y,
                    description=f"Door hinge line {door_thickness}mm",
                    layer=layer
                ))

                # 2. Door leaf: horizontal line in open position
                entities.append(Line(
                    x1=hinge_x, y1=hinge_end_y,
                    x2=hinge_x + door_leaf_length, y2=hinge_end_y,
                    description=f"Door leaf {door_leaf_length}mm",
                    layer=layer
                ))

                # 3. Swing arc: from open position (0°) to closed position (90°)
                entities.append(Arc(
                    center_x=hinge_x,
                    center_y=hinge_end_y,
                    radius=door_leaf_length,
                    start_angle=0.0,
                    end_angle=90.0,
                    description=f"Door swing arc {door_width}mm door",
                    layer=layer
                ))
            else:
                # Door swings outward (negative Y direction)
                hinge_end_y = hinge_y - door_thickness
                entities.append(Line(
                    x1=hinge_x, y1=hinge_y,
                    x2=hinge_x, y2=hinge_end_y,
                    description=f"Door hinge line {door_thickness}mm",
                    layer=layer
                ))
                entities.append(Line(
                    x1=hinge_x, y1=hinge_end_y,
                    x2=hinge_x + door_leaf_length, y2=hinge_end_y,
                    description=f"Door leaf {door_leaf_length}mm",
                    layer=layer
                ))
                entities.append(Arc(
                    center_x=hinge_x,
                    center_y=hinge_end_y,
                    radius=door_leaf_length,
                    start_angle=0.0,
                    end_angle=-90.0,
                    description=f"Door swing arc {door_width}mm door",
                    layer=layer
                ))

        else:  # Vertical wall
            hinge_x = wall_start_x
            hinge_y = wall_start_y + door_start

            if swing_inward:
                # Door swings into room (positive X direction)
                hinge_end_x = hinge_x + door_thickness
                entities.append(Line(
                    x1=hinge_x, y1=hinge_y,
                    x2=hinge_end_x, y2=hinge_y,
                    description=f"Door hinge line {door_thickness}mm",
                    layer=layer
                ))
                entities.append(Line(
                    x1=hinge_end_x, y1=hinge_y,
                    x2=hinge_end_x, y2=hinge_y + door_leaf_length,
                    description=f"Door leaf {door_leaf_length}mm",
                    layer=layer
                ))
                entities.append(Arc(
                    center_x=hinge_end_x,
                    center_y=hinge_y,
                    radius=door_leaf_length,
                    start_angle=90.0,
                    end_angle=180.0,
                    description=f"Door swing arc {door_width}mm door",
                    layer=layer
                ))
            else:
                # Door swings outward (negative X direction)
                hinge_end_x = hinge_x - door_thickness
                entities.append(Line(
                    x1=hinge_x, y1=hinge_y,
                    x2=hinge_end_x, y2=hinge_y,
                    description=f"Door hinge line {door_thickness}mm",
                    layer=layer
                ))
                entities.append(Line(
                    x1=hinge_end_x, y1=hinge_y,
                    x2=hinge_end_x, y2=hinge_y + door_leaf_length,
                    description=f"Door leaf {door_leaf_length}mm",
                    layer=layer
                ))
                entities.append(Arc(
                    center_x=hinge_end_x,
                    center_y=hinge_y,
                    radius=door_leaf_length,
                    start_angle=90.0,
                    end_angle=0.0,
                    description=f"Door swing arc {door_width}mm door",
                    layer=layer
                ))

        return entities
