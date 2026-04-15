"""2D Viewer - Generate SVG from DXF files or metadata.

This module provides SVG generation capabilities for 2D visualization
of DXF drawings, either from DXF files or directly from entity metadata.
"""

import math
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any


class DXF2DViewer:
    """Generate SVG visualizations from DXF files or entity metadata."""

    def __init__(self):
        self.stroke_width = 1
        self.stroke_color = "#000000"
        self.background = "#FFFFFF"
        self.padding = 20
        self.default_width = 800
        self.default_height = 600

    def from_dxf(self, dxf_path: str) -> Tuple[bool, str, str]:
        """Generate SVG from DXF file using ezdxf.

        Args:
            dxf_path: Path to the DXF file

        Returns:
            Tuple of (success, svg_content, error_message)
        """
        try:
            import ezdxf
            from ezdxf.addons.drawing import Frontend, RenderContext
            from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
            import io

            # Read the DXF file
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            # Extract entities and convert to our format
            entities = self._extract_entities_from_dxf(msp)

            # Generate SVG from entities
            return self.from_entities(entities)

        except ImportError as e:
            # Fall back to parsing DXF manually if ezdxf drawing addon unavailable
            return self._parse_dxf_manually(dxf_path)
        except Exception as e:
            return False, "", f"Error reading DXF: {str(e)}"

    def _extract_entities_from_dxf(self, msp) -> Dict[str, Any]:
        """Extract entities from ezdxf modelspace to our dictionary format."""
        entities = {
            'lines': [],
            'circles': [],
            'arcs': [],
            'polylines': [],
        }

        for entity in msp:
            dxftype = entity.dxftype()

            if dxftype == 'LINE':
                entities['lines'].append({
                    'x1': entity.dxf.start.x,
                    'y1': entity.dxf.start.y,
                    'x2': entity.dxf.end.x,
                    'y2': entity.dxf.end.y,
                    'layer': entity.dxf.layer
                })
            elif dxftype == 'CIRCLE':
                entities['circles'].append({
                    'center_x': entity.dxf.center.x,
                    'center_y': entity.dxf.center.y,
                    'radius': entity.dxf.radius,
                    'layer': entity.dxf.layer
                })
            elif dxftype == 'ARC':
                entities['arcs'].append({
                    'center_x': entity.dxf.center.x,
                    'center_y': entity.dxf.center.y,
                    'radius': entity.dxf.radius,
                    'start_angle': entity.dxf.start_angle,
                    'end_angle': entity.dxf.end_angle,
                    'layer': entity.dxf.layer
                })
            elif dxftype == 'LWPOLYLINE':
                points = []
                for x, y, *_ in entity.get_points():
                    points.append({'x': x, 'y': y})
                entities['polylines'].append({
                    'points': points,
                    'closed': entity.closed,
                    'layer': entity.dxf.layer
                })

        return entities

    def _parse_dxf_manually(self, dxf_path: str) -> Tuple[bool, str, str]:
        """Parse DXF file manually without ezdxf drawing addon."""
        try:
            with open(dxf_path, 'r') as f:
                content = f.read()

            entities = {
                'lines': [],
                'circles': [],
                'arcs': [],
                'polylines': [],
            }

            # Simple DXF parser - extract basic entities
            lines = content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                if line == '0' and i + 1 < len(lines):
                    entity_type = lines[i + 1].strip()

                    if entity_type == 'LINE':
                        line_data = self._parse_line_entity(lines, i)
                        if line_data:
                            entities['lines'].append(line_data)
                    elif entity_type == 'CIRCLE':
                        circle_data = self._parse_circle_entity(lines, i)
                        if circle_data:
                            entities['circles'].append(circle_data)
                    elif entity_type == 'ARC':
                        arc_data = self._parse_arc_entity(lines, i)
                        if arc_data:
                            entities['arcs'].append(arc_data)
                    elif entity_type == 'LWPOLYLINE':
                        poly_data = self._parse_polyline_entity(lines, i)
                        if poly_data:
                            entities['polylines'].append(poly_data)

                i += 1

            return self.from_entities(entities)

        except Exception as e:
            return False, "", f"Error parsing DXF: {str(e)}"

    def _parse_line_entity(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a LINE entity from DXF content."""
        data = {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0, 'layer': '0'}
        i = start_idx + 2

        while i < len(lines) and not (lines[i].strip() == '0' and i + 1 < len(lines) and lines[i + 1].strip() in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'ENDSEC', 'EOF']):
            code = lines[i].strip()
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                if code == '8':
                    data['layer'] = value
                elif code == '10':
                    data['x1'] = float(value)
                elif code == '20':
                    data['y1'] = float(value)
                elif code == '11':
                    data['x2'] = float(value)
                elif code == '21':
                    data['y2'] = float(value)
            i += 2

        return data

    def _parse_circle_entity(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a CIRCLE entity from DXF content."""
        data = {'center_x': 0, 'center_y': 0, 'radius': 1, 'layer': '0'}
        i = start_idx + 2

        while i < len(lines) and not (lines[i].strip() == '0' and i + 1 < len(lines) and lines[i + 1].strip() in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'ENDSEC', 'EOF']):
            code = lines[i].strip()
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                if code == '8':
                    data['layer'] = value
                elif code == '10':
                    data['center_x'] = float(value)
                elif code == '20':
                    data['center_y'] = float(value)
                elif code == '40':
                    data['radius'] = float(value)
            i += 2

        return data

    def _parse_arc_entity(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse an ARC entity from DXF content."""
        data = {'center_x': 0, 'center_y': 0, 'radius': 1, 'start_angle': 0, 'end_angle': 360, 'layer': '0'}
        i = start_idx + 2

        while i < len(lines) and not (lines[i].strip() == '0' and i + 1 < len(lines) and lines[i + 1].strip() in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'ENDSEC', 'EOF']):
            code = lines[i].strip()
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                if code == '8':
                    data['layer'] = value
                elif code == '10':
                    data['center_x'] = float(value)
                elif code == '20':
                    data['center_y'] = float(value)
                elif code == '40':
                    data['radius'] = float(value)
                elif code == '50':
                    data['start_angle'] = float(value)
                elif code == '51':
                    data['end_angle'] = float(value)
            i += 2

        return data

    def _parse_polyline_entity(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a LWPOLYLINE entity from DXF content."""
        data = {'points': [], 'closed': False, 'layer': '0'}
        i = start_idx + 2
        current_x = None

        while i < len(lines):
            code = lines[i].strip()

            # Check for end of entity
            if code == '0' and i + 1 < len(lines):
                next_val = lines[i + 1].strip()
                if next_val in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'ENDSEC', 'EOF', 'HATCH', 'TEXT', 'POINT']:
                    break

            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                if code == '8':
                    data['layer'] = value
                elif code == '70':
                    # Flags: 1 = closed
                    data['closed'] = (int(value) & 1) == 1
                elif code == '10':
                    current_x = float(value)
                elif code == '20' and current_x is not None:
                    data['points'].append({'x': current_x, 'y': float(value)})
                    current_x = None
            i += 2

        return data if data['points'] else None

    def from_metadata(self, csv_metadata: str) -> Tuple[bool, str, str]:
        """Generate SVG from CSV metadata directly.

        Args:
            csv_metadata: The CSV metadata string in text_to_dxf format

        Returns:
            Tuple of (success, svg_content, error_message)
        """
        try:
            entities = self._parse_csv_metadata(csv_metadata)
            return self.from_entities(entities)
        except Exception as e:
            return False, "", f"Error parsing metadata: {str(e)}"

    def _parse_csv_metadata(self, csv_metadata: str) -> Dict[str, Any]:
        """Parse CSV metadata into entities dictionary."""
        entities = {
            'lines': [],
            'circles': [],
            'arcs': [],
            'polylines': [],
        }

        lines = csv_metadata.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 2:
                continue

            entity_type = parts[0].upper()

            if entity_type == 'LINE' and len(parts) >= 5:
                entities['lines'].append({
                    'x1': float(parts[1]),
                    'y1': float(parts[2]),
                    'x2': float(parts[3]),
                    'y2': float(parts[4]),
                    'layer': parts[5] if len(parts) > 5 else '0'
                })
            elif entity_type == 'CIRCLE' and len(parts) >= 4:
                entities['circles'].append({
                    'center_x': float(parts[1]),
                    'center_y': float(parts[2]),
                    'radius': float(parts[3]),
                    'layer': parts[4] if len(parts) > 4 else '0'
                })
            elif entity_type == 'ARC' and len(parts) >= 6:
                entities['arcs'].append({
                    'center_x': float(parts[1]),
                    'center_y': float(parts[2]),
                    'radius': float(parts[3]),
                    'start_angle': float(parts[4]),
                    'end_angle': float(parts[5]),
                    'layer': parts[6] if len(parts) > 6 else '0'
                })
            elif entity_type == 'POLYLINE' and len(parts) >= 3:
                # POLYLINE, x1, y1, x2, y2, ..., closed, layer
                points = []
                i = 1
                while i + 1 < len(parts):
                    try:
                        x = float(parts[i])
                        y = float(parts[i + 1])
                        points.append({'x': x, 'y': y})
                        i += 2
                    except ValueError:
                        break

                # Check for closed flag and layer
                closed = False
                layer = '0'
                remaining = parts[i:]
                for item in remaining:
                    if item.lower() in ('true', '1', 'closed'):
                        closed = True
                    elif item and not item.lower() in ('false', '0'):
                        layer = item

                if points:
                    entities['polylines'].append({
                        'points': points,
                        'closed': closed,
                        'layer': layer
                    })
            elif entity_type == 'RECTANGLE' and len(parts) >= 5:
                # RECTANGLE, x, y, width, height, layer
                x = float(parts[1])
                y = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
                layer = parts[5] if len(parts) > 5 else '0'

                # Convert rectangle to polyline
                entities['polylines'].append({
                    'points': [
                        {'x': x, 'y': y},
                        {'x': x + w, 'y': y},
                        {'x': x + w, 'y': y + h},
                        {'x': x, 'y': y + h}
                    ],
                    'closed': True,
                    'layer': layer
                })

        return entities

    def from_entities(self, entities: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Generate SVG from entity dictionary.

        Args:
            entities: Dictionary with 'lines', 'circles', 'arcs', 'polylines'

        Returns:
            Tuple of (success, svg_content, error_message)
        """
        try:
            # Calculate bounding box
            min_x, min_y, max_x, max_y = self._calculate_bounds(entities)

            if min_x == float('inf'):
                return False, "", "No entities to render"

            # Add padding
            width = max_x - min_x + 2 * self.padding
            height = max_y - min_y + 2 * self.padding

            # Scale to fit default dimensions while maintaining aspect ratio
            scale_x = self.default_width / width if width > 0 else 1
            scale_y = self.default_height / height if height > 0 else 1
            scale = min(scale_x, scale_y)

            svg_width = width * scale
            svg_height = height * scale

            # Build SVG
            svg_elements = []

            # Transform function to map DXF coords to SVG coords
            def transform(x: float, y: float) -> Tuple[float, float]:
                # DXF uses bottom-left origin, SVG uses top-left
                # Flip Y axis and apply offset and scale
                svg_x = (x - min_x + self.padding) * scale
                svg_y = (max_y - y + self.padding) * scale
                return svg_x, svg_y

            # Render lines
            for line in entities.get('lines', []):
                x1, y1 = transform(line['x1'], line['y1'])
                x2, y2 = transform(line['x2'], line['y2'])
                svg_elements.append(
                    f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                    f'stroke="{self.stroke_color}" stroke-width="{self.stroke_width}"/>'
                )

            # Render circles
            for circle in entities.get('circles', []):
                cx, cy = transform(circle['center_x'], circle['center_y'])
                r = circle['radius'] * scale
                svg_elements.append(
                    f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                    f'stroke="{self.stroke_color}" stroke-width="{self.stroke_width}" fill="none"/>'
                )

            # Render arcs
            for arc in entities.get('arcs', []):
                arc_path = self._arc_to_svg_path(arc, transform, scale)
                if arc_path:
                    svg_elements.append(
                        f'<path d="{arc_path}" stroke="{self.stroke_color}" '
                        f'stroke-width="{self.stroke_width}" fill="none"/>'
                    )

            # Render polylines
            for polyline in entities.get('polylines', []):
                points = polyline.get('points', [])
                if len(points) < 2:
                    continue

                # Convert points to SVG path
                path_parts = []
                for i, pt in enumerate(points):
                    sx, sy = transform(pt['x'], pt['y'])
                    if i == 0:
                        path_parts.append(f"M {sx:.2f} {sy:.2f}")
                    else:
                        path_parts.append(f"L {sx:.2f} {sy:.2f}")

                if polyline.get('closed', False):
                    path_parts.append("Z")

                svg_elements.append(
                    f'<path d="{" ".join(path_parts)}" stroke="{self.stroke_color}" '
                    f'stroke-width="{self.stroke_width}" fill="none"/>'
                )

            # Build complete SVG
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{svg_width:.2f}" height="{svg_height:.2f}"
     viewBox="0 0 {svg_width:.2f} {svg_height:.2f}"
     style="background-color: {self.background}">
  <g id="entities">
    {chr(10).join("    " + elem for elem in svg_elements)}
  </g>
</svg>'''

            return True, svg_content, ""

        except Exception as e:
            return False, "", f"Error generating SVG: {str(e)}"

    def _calculate_bounds(self, entities: Dict[str, Any]) -> Tuple[float, float, float, float]:
        """Calculate bounding box of all entities."""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        # Lines
        for line in entities.get('lines', []):
            min_x = min(min_x, line['x1'], line['x2'])
            min_y = min(min_y, line['y1'], line['y2'])
            max_x = max(max_x, line['x1'], line['x2'])
            max_y = max(max_y, line['y1'], line['y2'])

        # Circles
        for circle in entities.get('circles', []):
            r = circle['radius']
            min_x = min(min_x, circle['center_x'] - r)
            min_y = min(min_y, circle['center_y'] - r)
            max_x = max(max_x, circle['center_x'] + r)
            max_y = max(max_y, circle['center_y'] + r)

        # Arcs
        for arc in entities.get('arcs', []):
            r = arc['radius']
            min_x = min(min_x, arc['center_x'] - r)
            min_y = min(min_y, arc['center_y'] - r)
            max_x = max(max_x, arc['center_x'] + r)
            max_y = max(max_y, arc['center_y'] + r)

        # Polylines
        for polyline in entities.get('polylines', []):
            for pt in polyline.get('points', []):
                min_x = min(min_x, pt['x'])
                min_y = min(min_y, pt['y'])
                max_x = max(max_x, pt['x'])
                max_y = max(max_y, pt['y'])

        return min_x, min_y, max_x, max_y

    def _arc_to_svg_path(self, arc: Dict, transform, scale: float) -> str:
        """Convert a DXF arc to SVG path."""
        cx = arc['center_x']
        cy = arc['center_y']
        r = arc['radius']
        start_angle = math.radians(arc['start_angle'])
        end_angle = math.radians(arc['end_angle'])

        # Calculate start and end points
        start_x = cx + r * math.cos(start_angle)
        start_y = cy + r * math.sin(start_angle)
        end_x = cx + r * math.cos(end_angle)
        end_y = cy + r * math.sin(end_angle)

        # Transform to SVG coordinates
        sx1, sy1 = transform(start_x, start_y)
        sx2, sy2 = transform(end_x, end_y)
        svg_r = r * scale

        # Calculate arc sweep
        sweep_angle = end_angle - start_angle
        if sweep_angle < 0:
            sweep_angle += 2 * math.pi

        large_arc = 1 if sweep_angle > math.pi else 0
        # SVG arc direction is opposite due to Y-flip
        sweep_flag = 0  # Counter-clockwise in SVG space

        return f"M {sx1:.2f} {sy1:.2f} A {svg_r:.2f} {svg_r:.2f} 0 {large_arc} {sweep_flag} {sx2:.2f} {sy2:.2f}"

    def launch_external_viewer(self, file_path: str) -> Tuple[bool, str]:
        """Launch an external viewer application for the file.

        Args:
            file_path: Path to the file to view

        Returns:
            Tuple of (success, error_message)
        """
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {file_path}"

        # List of viewers to try (Linux-focused)
        viewers = [
            'xdg-open',  # Generic Linux opener
            'eog',       # GNOME Eye of GNOME
            'feh',       # Lightweight image viewer
            'display',   # ImageMagick
            'inkscape',  # For SVG files
            'evince',    # PDF viewer
            'okular',    # KDE document viewer
        ]

        ext = path.suffix.lower()

        # Prefer specific viewers for certain formats
        if ext == '.svg':
            viewers = ['inkscape', 'xdg-open', 'eog', 'feh', 'display']
        elif ext == '.pdf':
            viewers = ['evince', 'okular', 'xdg-open']
        elif ext in ['.png', '.jpg', '.jpeg']:
            viewers = ['eog', 'feh', 'display', 'xdg-open']
        elif ext == '.dxf':
            # For DXF, try to convert to SVG first and display that
            success, svg_content, error = self.from_dxf(file_path)
            if success:
                svg_path = path.with_suffix('.svg')
                svg_path.write_text(svg_content)
                file_path = str(svg_path)
                viewers = ['inkscape', 'xdg-open', 'eog', 'feh', 'display']

        # Try each viewer
        for viewer in viewers:
            if shutil.which(viewer):
                try:
                    subprocess.Popen(
                        [viewer, file_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return True, ""
                except Exception as e:
                    continue

        return False, "No suitable viewer found. Install eog, feh, or inkscape."


# Module-level instance for easy access
viewer_2d = DXF2DViewer()
