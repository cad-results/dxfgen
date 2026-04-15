"""Minimal DXF Writer - Generates clean, non-bloated DXF files.

This writer creates DXF files in R2000 (AC1015) format, which:
- Supports LWPOLYLINE with proper subclass markers for modern readers
- Is compatible with most CAD software including ezdxf
- Minimal boilerplate (~50-100 lines for simple drawings vs 400+ with ezdxf)
- Contains only essential sections: HEADER, ENTITIES, EOF

DXF format reference:
- Group codes (first line) define the type of data
- Values (second line) contain the actual data
- Common codes: 0=entity type, 5=handle, 8=layer, 10/20=X/Y coords, 40=radius
- 100=subclass marker (AcDbEntity, AcDbPolyline, etc.)
"""

from typing import List, Tuple, Optional
from pathlib import Path


class MinimalDXFWriter:
    """Writes minimal, clean DXF files without bloat."""

    def __init__(self):
        self.entities: List[str] = []
        self.layers: set = {"0"}  # Default layer always exists
        self._handle_counter: int = 100  # Start entity handles at 100

    def _next_handle(self) -> str:
        """Get the next unique entity handle as a hex string."""
        h = format(self._handle_counter, 'X')
        self._handle_counter += 1
        return h

    def _ensure_layer(self, layer: str) -> None:
        """Track layer for potential TABLES section."""
        if layer:
            self.layers.add(layer)

    def add_line(self, x1: float, y1: float, x2: float, y2: float,
                 layer: str = "0") -> None:
        """Add a LINE entity.

        Args:
            x1, y1: Start point
            x2, y2: End point
            layer: Layer name
        """
        self._ensure_layer(layer)
        handle = self._next_handle()
        self.entities.append(f"""0
LINE
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbLine
10
{x1}
20
{y1}
11
{x2}
21
{y2}""")

    def add_circle(self, center_x: float, center_y: float, radius: float,
                   layer: str = "0") -> None:
        """Add a CIRCLE entity.

        Args:
            center_x, center_y: Center point
            radius: Circle radius
            layer: Layer name
        """
        self._ensure_layer(layer)
        handle = self._next_handle()
        self.entities.append(f"""0
CIRCLE
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbCircle
10
{center_x}
20
{center_y}
40
{radius}""")

    def add_arc(self, center_x: float, center_y: float, radius: float,
                start_angle: float, end_angle: float, layer: str = "0") -> None:
        """Add an ARC entity.

        Args:
            center_x, center_y: Center point
            radius: Arc radius
            start_angle: Start angle in degrees
            end_angle: End angle in degrees
            layer: Layer name
        """
        self._ensure_layer(layer)
        handle = self._next_handle()
        self.entities.append(f"""0
ARC
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbCircle
10
{center_x}
20
{center_y}
40
{radius}
100
AcDbArc
50
{start_angle}
51
{end_angle}""")

    def add_polyline(self, points: List[Tuple[float, float]],
                     closed: bool = False, layer: str = "0") -> None:
        """Add a LWPOLYLINE entity (lightweight polyline).

        Args:
            points: List of (x, y) tuples
            closed: Whether to close the polyline
            layer: Layer name
        """
        if not points:
            return

        self._ensure_layer(layer)

        # LWPOLYLINE format with proper subclass markers for R2000+
        handle = self._next_handle()
        num_vertices = len(points)
        flags = 1 if closed else 0

        lines = [f"""0
LWPOLYLINE
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbPolyline
90
{num_vertices}
70
{flags}"""]

        # Add each vertex
        for x, y in points:
            lines.append(f"""10
{x}
20
{y}""")

        self.entities.append("\n".join(lines))

    def add_polyline_with_bulge(self, vertices: List[Tuple[float, float, float, float, float]],
                                 closed: bool = False, layer: str = "0") -> None:
        """Add a LWPOLYLINE with width and bulge values.

        Args:
            vertices: List of (x, y, start_width, end_width, bulge) tuples
            closed: Whether to close the polyline
            layer: Layer name
        """
        if not vertices:
            return

        self._ensure_layer(layer)

        handle = self._next_handle()
        num_vertices = len(vertices)
        flags = 1 if closed else 0

        lines = [f"""0
LWPOLYLINE
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbPolyline
90
{num_vertices}
70
{flags}"""]

        # Add each vertex with width and bulge
        for x, y, sw, ew, bulge in vertices:
            vertex_data = f"""10
{x}
20
{y}"""
            if sw != 0:
                vertex_data += f"\n40\n{sw}"
            if ew != 0:
                vertex_data += f"\n41\n{ew}"
            if bulge != 0:
                vertex_data += f"\n42\n{bulge}"
            lines.append(vertex_data)

        self.entities.append("\n".join(lines))

    def add_hatch(self, boundary_points: List[Tuple[float, float]],
                  pattern: str = "SOLID", layer: str = "0") -> None:
        """Add a simple HATCH entity with polyline boundary.

        This creates a simple solid hatch with a polyline boundary.

        Args:
            boundary_points: List of (x, y) boundary points
            pattern: Hatch pattern name (SOLID for filled)
            layer: Layer name
        """
        if not boundary_points or len(boundary_points) < 3:
            return

        self._ensure_layer(layer)

        handle = self._next_handle()
        num_points = len(boundary_points)

        # Build boundary path vertices
        boundary_vertices = ""
        for x, y in boundary_points:
            boundary_vertices += f"10\n{x}\n20\n{y}\n"

        # HATCH with proper subclass markers for R2000+
        self.entities.append(f"""0
HATCH
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbHatch
10
0.0
20
0.0
30
0.0
210
0.0
220
0.0
230
1.0
2
{pattern}
70
1
71
0
91
1
92
1
93
{num_points}
{boundary_vertices.rstrip()}
97
0""")

    def add_point(self, x: float, y: float, layer: str = "0") -> None:
        """Add a POINT entity.

        Args:
            x, y: Point coordinates
            layer: Layer name
        """
        self._ensure_layer(layer)
        handle = self._next_handle()
        self.entities.append(f"""0
POINT
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbPoint
10
{x}
20
{y}""")

    def add_text(self, x: float, y: float, text: str, height: float = 2.5,
                 layer: str = "0") -> None:
        """Add a TEXT entity.

        Args:
            x, y: Text insertion point
            text: Text content
            height: Text height
            layer: Layer name
        """
        self._ensure_layer(layer)
        handle = self._next_handle()
        self.entities.append(f"""0
TEXT
5
{handle}
100
AcDbEntity
8
{layer}
100
AcDbText
10
{x}
20
{y}
40
{height}
1
{text}
100
AcDbText""")

    def _build_header(self) -> str:
        """Build the minimal HEADER section for R2000 (AC1015) format."""
        return """0
SECTION
2
HEADER
9
$ACADVER
1
AC1015
9
$INSUNITS
70
4
0
ENDSEC"""

    def _build_tables(self) -> str:
        """Build TABLES section with layer definitions.

        Note: For true R12 compatibility, this is optional.
        Layers are auto-created on entity use in most CAD software.
        """
        # Skip tables for minimal output - layers auto-create
        return ""

    def _build_entities(self) -> str:
        """Build the ENTITIES section."""
        if not self.entities:
            return """0
SECTION
2
ENTITIES
0
ENDSEC"""

        entity_content = "\n".join(self.entities)
        return f"""0
SECTION
2
ENTITIES
{entity_content}
0
ENDSEC"""

    def _build_eof(self) -> str:
        """Build the EOF marker."""
        return """0
EOF"""

    def to_string(self) -> str:
        """Generate the complete DXF content as a string."""
        sections = [
            self._build_header(),
            self._build_entities(),
            self._build_eof()
        ]
        return "\n".join(sections)

    def save(self, filepath: str) -> None:
        """Save the DXF content to a file.

        Args:
            filepath: Output file path
        """
        content = self.to_string()
        Path(filepath).write_text(content)

    def clear(self) -> None:
        """Clear all entities for reuse."""
        self.entities = []
        self.layers = {"0"}
        self._handle_counter = 100


def create_minimal_dxf(entities_dict: dict, output_path: str) -> bool:
    """Convenience function to create a minimal DXF from an entities dictionary.

    Args:
        entities_dict: Dictionary with 'lines', 'circles', 'arcs', 'polylines', 'hatches'
        output_path: Output file path

    Returns:
        True if successful
    """
    writer = MinimalDXFWriter()

    # Add lines
    for line in entities_dict.get('lines', []):
        writer.add_line(
            line.get('x1', 0), line.get('y1', 0),
            line.get('x2', 0), line.get('y2', 0),
            line.get('layer', '0')
        )

    # Add circles
    for circle in entities_dict.get('circles', []):
        writer.add_circle(
            circle.get('center_x', 0), circle.get('center_y', 0),
            circle.get('radius', 0),
            circle.get('layer', '0')
        )

    # Add arcs
    for arc in entities_dict.get('arcs', []):
        writer.add_arc(
            arc.get('center_x', 0), arc.get('center_y', 0),
            arc.get('radius', 0),
            arc.get('start_angle', 0), arc.get('end_angle', 360),
            arc.get('layer', '0')
        )

    # Add polylines
    for polyline in entities_dict.get('polylines', []):
        points = [(p.get('x', 0), p.get('y', 0)) for p in polyline.get('points', [])]
        writer.add_polyline(
            points,
            polyline.get('closed', False),
            polyline.get('layer', '0')
        )

    # Add hatches
    for hatch in entities_dict.get('hatches', []):
        boundary = [(p.get('x', 0), p.get('y', 0)) for p in hatch.get('boundary_points', [])]
        writer.add_hatch(
            boundary,
            hatch.get('pattern', 'SOLID'),
            hatch.get('layer', '0')
        )

    # Add polylines with curves (bulge)
    for pw in entities_dict.get('polylines_with_curves', []):
        vertices = []
        for v in pw.get('vertices', []):
            vertices.append((
                v.get('x', 0), v.get('y', 0),
                v.get('start_width', 0), v.get('end_width', 0),
                v.get('bulge', 0)
            ))
        writer.add_polyline_with_bulge(
            vertices,
            pw.get('closed', False),
            pw.get('layer', '0')
        )

    writer.save(output_path)
    return True
