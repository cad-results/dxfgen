"""DXF Generator - Integrates with text_to_dxf to create DXF files.

Supports both basic entities (lines, circles, arcs, polylines, hatches)
and advanced curve entities (splines, NURBS, Bezier, ellipses).

Includes minimal DXF writer for clean, non-bloated output.
"""

import os
import sys
import subprocess
import tempfile
import math
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import ezdxf

from .minimal_dxf_writer import MinimalDXFWriter, create_minimal_dxf


class DXFGenerator:
    """Generates DXF files from CSV metadata using text_to_dxf."""

    def __init__(self, text_to_dxf_path: Optional[str] = None):
        """Initialize the DXF generator.

        Args:
            text_to_dxf_path: Path to text_to_dxf directory. If None, uses default.
        """
        if text_to_dxf_path is None:
            # Default to backend/text_to_dxf
            self.text_to_dxf_path = Path(__file__).parent / "text_to_dxf"
        else:
            self.text_to_dxf_path = Path(text_to_dxf_path)

        self.script_path = self.text_to_dxf_path / "text_to_dxf.py"

        if not self.script_path.exists():
            raise FileNotFoundError(f"text_to_dxf.py not found at {self.script_path}")

    def generate(self, csv_metadata: str, output_filename: str = None) -> tuple[bool, str, str]:
        """Generate a DXF file from CSV metadata.

        Args:
            csv_metadata: CSV format metadata string
            output_filename: Optional output filename (without path)

        Returns:
            Tuple of (success, output_path, error_message)
        """
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_input:
            temp_input.write(csv_metadata)
            input_path = temp_input.name

        try:
            # Determine output path
            output_dir = Path(__file__).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)

            if output_filename is None:
                import time
                output_filename = f"drawing_{int(time.time())}.dxf"
            elif not output_filename.endswith('.dxf'):
                output_filename += '.dxf'

            output_path = output_dir / output_filename

            # Run text_to_dxf.py
            result = subprocess.run(
                [sys.executable, str(self.script_path), input_path, str(output_path)],
                capture_output=True,
                text=True,
                cwd=str(self.text_to_dxf_path)
            )

            # Check if successful
            if result.returncode == 0 and output_path.exists():
                return True, str(output_path), ""
            else:
                error_msg = f"Return code: {result.returncode}\n"
                if result.stderr:
                    error_msg += f"STDERR: {result.stderr}\n"
                if result.stdout:
                    error_msg += f"STDOUT: {result.stdout}"
                if not error_msg.strip():
                    error_msg = "Unknown error occurred"
                return False, "", error_msg

        except Exception as e:
            return False, "", str(e)

        finally:
            # Clean up temporary input file
            try:
                os.unlink(input_path)
            except:
                pass

    def generate_from_file(self, input_file: str, output_file: str) -> tuple[bool, str, str]:
        """Generate a DXF file from a CSV file.

        Args:
            input_file: Path to input CSV file
            output_file: Path to output DXF file

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            result = subprocess.run(
                [sys.executable, str(self.script_path), input_file, output_file],
                capture_output=True,
                text=True,
                cwd=str(self.text_to_dxf_path)
            )

            if result.returncode == 0 and Path(output_file).exists():
                return True, output_file, ""
            else:
                error_msg = f"Return code: {result.returncode}\n"
                if result.stderr:
                    error_msg += f"STDERR: {result.stderr}\n"
                if result.stdout:
                    error_msg += f"STDOUT: {result.stdout}"
                if not error_msg.strip():
                    error_msg = "Unknown error occurred"
                return False, "", error_msg

        except Exception as e:
            return False, "", str(e)

    def generate_with_curves(
        self,
        entities_dict: Dict[str, Any],
        output_filename: str = None
    ) -> tuple[bool, str, str]:
        """
        Generate a DXF file with support for advanced curve entities.

        Uses ezdxf directly to support:
        - B-Spline curves
        - NURBS curves
        - Bezier curves
        - Ellipses and elliptical arcs
        - Polylines with curved segments (bulge)

        Args:
            entities_dict: Dictionary of entities from ExtendedEntities.model_dump()
            output_filename: Optional output filename

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            # Create new DXF document
            doc = ezdxf.new('R2010')  # AutoCAD 2010 format for spline support
            msp = doc.modelspace()

            # Track created layers
            created_layers = set()

            def ensure_layer(layer_name: str):
                """Create layer if it doesn't exist."""
                if layer_name not in created_layers:
                    if layer_name != "0":
                        doc.layers.new(name=layer_name)
                    created_layers.add(layer_name)

            # Process basic entities
            self._add_basic_entities(msp, entities_dict, ensure_layer)

            # Process curve entities
            self._add_curve_entities(msp, entities_dict, ensure_layer)

            # Determine output path
            output_dir = Path(__file__).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)

            if output_filename is None:
                import time
                output_filename = f"drawing_{int(time.time())}.dxf"
            elif not output_filename.endswith('.dxf'):
                output_filename += '.dxf'

            output_path = output_dir / output_filename

            # Save DXF file
            doc.saveas(str(output_path))

            return True, str(output_path), ""

        except Exception as e:
            import traceback
            return False, "", f"{str(e)}\n{traceback.format_exc()}"

    def _add_basic_entities(
        self,
        msp,
        entities_dict: Dict[str, Any],
        ensure_layer
    ):
        """Add basic entities (lines, circles, arcs, polylines, hatches) to modelspace."""

        # Lines
        for line in entities_dict.get('lines', []):
            layer = line.get('layer', '0')
            ensure_layer(layer)
            msp.add_line(
                (line['x1'], line['y1']),
                (line['x2'], line['y2']),
                dxfattribs={'layer': layer}
            )

        # Circles
        for circle in entities_dict.get('circles', []):
            layer = circle.get('layer', '0')
            ensure_layer(layer)
            msp.add_circle(
                (circle['center_x'], circle['center_y']),
                circle['radius'],
                dxfattribs={'layer': layer}
            )

        # Arcs
        for arc in entities_dict.get('arcs', []):
            layer = arc.get('layer', '0')
            ensure_layer(layer)
            msp.add_arc(
                (arc['center_x'], arc['center_y']),
                arc['radius'],
                arc['start_angle'],
                arc['end_angle'],
                dxfattribs={'layer': layer}
            )

        # Polylines
        for polyline in entities_dict.get('polylines', []):
            layer = polyline.get('layer', '0')
            ensure_layer(layer)
            points = [(p['x'], p['y']) for p in polyline.get('points', [])]
            if points:
                pline = msp.add_lwpolyline(points, dxfattribs={'layer': layer})
                if polyline.get('closed', False):
                    pline.close()

        # Hatches
        for hatch_data in entities_dict.get('hatches', []):
            layer = hatch_data.get('layer', '0')
            ensure_layer(layer)
            points = [(p['x'], p['y']) for p in hatch_data.get('boundary_points', [])]
            if points:
                hatch = msp.add_hatch(dxfattribs={'layer': layer})
                hatch.paths.add_polyline_path(points, is_closed=True)

    def _add_curve_entities(
        self,
        msp,
        entities_dict: Dict[str, Any],
        ensure_layer
    ):
        """Add curve entities (splines, NURBS, Bezier, ellipses) to modelspace."""

        # B-Splines
        for spline_data in entities_dict.get('splines', []):
            layer = spline_data.get('layer', '0')
            ensure_layer(layer)

            degree = spline_data.get('degree', 3)
            fit_points = spline_data.get('fit_points', [])
            control_points = spline_data.get('control_points', [])
            closed = spline_data.get('closed', False)

            if fit_points:
                # Create interpolating spline from fit points
                fit_pts_3d = [(p['x'], p['y'], 0) for p in fit_points]
                spline = msp.add_spline(
                    fit_points=fit_pts_3d,
                    degree=degree,
                    dxfattribs={'layer': layer}
                )
                if closed:
                    spline.set_closed()
            elif control_points:
                # Create spline from control points using add_open_spline
                ctrl_pts_3d = [(p['x'], p['y'], 0) for p in control_points]

                if closed:
                    # For closed splines, create and set closed flag
                    spline = msp.add_spline(dxfattribs={'layer': layer})
                    spline.control_points = ctrl_pts_3d
                    spline.dxf.degree = degree
                    spline.set_closed()
                else:
                    # For open splines, use add_open_spline
                    spline = msp.add_open_spline(ctrl_pts_3d, degree=degree, dxfattribs={'layer': layer})

                # Set knots if provided
                knots = spline_data.get('knots')
                if knots:
                    spline.knots = knots

        # NURBS curves
        for nurbs_data in entities_dict.get('nurbs_curves', []):
            layer = nurbs_data.get('layer', '0')
            ensure_layer(layer)

            control_points = nurbs_data.get('control_points', [])
            if control_points:
                # Extract coordinates and weights
                ctrl_pts_3d = [(p['x'], p['y'], 0) for p in control_points]
                weights = [p.get('weight', 1.0) for p in control_points]
                degree = nurbs_data.get('degree', 3)
                knots = nurbs_data.get('knots')

                msp.add_rational_spline(
                    control_points=ctrl_pts_3d,
                    weights=weights,
                    degree=degree,
                    knots=knots,
                    dxfattribs={'layer': layer}
                )

        # Bezier curves
        for bezier_data in entities_dict.get('bezier_curves', []):
            layer = bezier_data.get('layer', '0')
            ensure_layer(layer)

            control_points = bezier_data.get('control_points', [])
            if control_points:
                ctrl_pts_3d = [(p['x'], p['y'], 0) for p in control_points]
                degree = len(control_points) - 1

                # Bezier is a special case of B-spline with specific knot vector
                # Knots: [0]*(degree+1) + [1]*(degree+1)
                knots = [0.0] * (degree + 1) + [1.0] * (degree + 1)

                spline = msp.add_spline(dxfattribs={'layer': layer})
                spline.control_points = ctrl_pts_3d
                spline.dxf.degree = degree
                spline.knots = knots

        # Ellipses
        for ellipse_data in entities_dict.get('ellipses', []):
            layer = ellipse_data.get('layer', '0')
            ensure_layer(layer)

            center = (ellipse_data['center_x'], ellipse_data['center_y'], 0)
            major_axis = (
                ellipse_data['major_axis_x'],
                ellipse_data['major_axis_y'],
                0
            )
            ratio = ellipse_data.get('ratio', 1.0)
            start_param = ellipse_data.get('start_param', 0)
            end_param = ellipse_data.get('end_param', 2 * math.pi)

            msp.add_ellipse(
                center=center,
                major_axis=major_axis,
                ratio=ratio,
                start_param=start_param,
                end_param=end_param,
                dxfattribs={'layer': layer}
            )

        # Polylines with curves (bulge values)
        for pw_data in entities_dict.get('polylines_with_curves', []):
            layer = pw_data.get('layer', '0')
            ensure_layer(layer)

            vertices = pw_data.get('vertices', [])
            if vertices:
                # Format: (x, y, start_width, end_width, bulge)
                points = []
                for v in vertices:
                    # Handle both dict and object (Pydantic model) formats
                    if isinstance(v, dict):
                        x = v.get('x', 0)
                        y = v.get('y', 0)
                        sw = v.get('start_width', 0)
                        ew = v.get('end_width', 0)
                        bulge = v.get('bulge', 0)
                    else:
                        x = getattr(v, 'x', 0)
                        y = getattr(v, 'y', 0)
                        sw = getattr(v, 'start_width', 0)
                        ew = getattr(v, 'end_width', 0)
                        bulge = getattr(v, 'bulge', 0)
                    points.append((x, y, sw, ew, bulge))

                pline = msp.add_lwpolyline(points, dxfattribs={'layer': layer})
                if pw_data.get('closed', False):
                    pline.close()

    def generate_from_entities(
        self,
        entities_dict: Dict[str, Any],
        output_filename: str = None,
        use_minimal_format: bool = True
    ) -> tuple[bool, str, str]:
        """Generate DXF directly from entity objects, bypassing CSV parsing.

        This method provides a more reliable generation path that avoids
        the error-prone CSV intermediate format.

        Args:
            entities_dict: Dictionary with entity lists (lines, circles, arcs, etc.)
            output_filename: Optional output filename
            use_minimal_format: If True, use minimal R12 format (smaller files).
                               If False, use ezdxf R2010 format (curve support).

        Returns:
            Tuple of (success, output_path, error_message)
        """
        try:
            # Determine output path
            output_dir = Path(__file__).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)

            if output_filename is None:
                import time
                output_filename = f"drawing_{int(time.time())}.dxf"
            elif not output_filename.endswith('.dxf'):
                output_filename += '.dxf'

            output_path = output_dir / output_filename

            # Check if we need advanced curve support
            has_advanced_curves = any(
                key in entities_dict and entities_dict[key]
                for key in ['splines', 'nurbs_curves', 'bezier_curves', 'ellipses']
            )

            if has_advanced_curves or not use_minimal_format:
                # Use ezdxf for advanced curves (splines, NURBS, etc.)
                return self.generate_with_curves(entities_dict, output_filename)

            # Use minimal DXF writer for basic entities
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
                points_data = polyline.get('points', [])
                points = [(p.get('x', 0), p.get('y', 0)) for p in points_data]
                writer.add_polyline(
                    points,
                    polyline.get('closed', False),
                    polyline.get('layer', '0')
                )

            # Add hatches
            for hatch in entities_dict.get('hatches', []):
                boundary_data = hatch.get('boundary_points', [])
                boundary = [(p.get('x', 0), p.get('y', 0)) for p in boundary_data]
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

            # Save the file
            writer.save(str(output_path))

            return True, str(output_path), ""

        except Exception as e:
            import traceback
            return False, "", f"{str(e)}\n{traceback.format_exc()}"
