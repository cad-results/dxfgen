"""Metadata Formatter Agent - Converts entities to text_to_dxf CSV format."""

from typing import Dict, Any, List, Union
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import math

from .entity_extractor import ExtractedEntities, Line, Circle, Arc, Polyline, Hatch, Point
from .curve_entities import (
    ExtendedEntities, Spline, NURBSCurve, BezierCurve, Ellipse, PolylineWithCurves
)


class MetadataFormatterAgent:
    """Agent that formats extracted entities into text_to_dxf CSV format.

    Format specification from text_to_dxf:
    - Header format: type, description, show_line, layer
      - type: L (line), C (circle), A (arc), P (polyline), H (hatch)
      - description: Text description of the entity
      - show_line: 1 to show the entity, 0 to hide
      - layer: Layer name (string)

    - Lines (L): x1, y1, x2, y2
    - Circles (C): center_x, center_y, radius
    - Arcs (A): center_x, center_y, radius, start_angle, end_angle
    - Polylines (P): x1, y1, x2, y2, x3, y3, ... (pairs of coordinates)
    - Hatches (H): x1, y1, x2, y2, x3, y3, ... (boundary points)

    Example:
        L, Wall, 1, WALLS
        0, 0
        100, 0

        C, Window, 1, DETAILS
        50, 50, 20

    Note: Text annotations (room labels, dimensions) are supported via the
    'description' field in the header, which text_to_dxf renders as text
    at the bottom of each figure. For professional annotations, use descriptive
    text in the description field (e.g., "Living Room 5m × 4m", "Bedroom 1").
    """

    def __init__(self, llm: ChatOpenAI = None):
        self.llm = llm  # Optional, for advanced formatting decisions

    def format_line(self, line: Line) -> str:
        """Format a line entity to CSV format.

        text_to_dxf format requires each point on its own line:
        L,Description,1,Layer
        x1,y1
        x2,y2

        Note: No spaces after commas in coordinate data as text_to_dxf parser
        doesn't strip whitespace from numeric values.
        """
        header = f"{line.type},{line.description},1,{line.layer}"
        point1 = f"{line.x1},{line.y1}"
        point2 = f"{line.x2},{line.y2}"
        return f"{header}\n{point1}\n{point2}"

    def format_circle(self, circle: Circle) -> str:
        """Format a circle entity to CSV format."""
        header = f"{circle.type},{circle.description},1,{circle.layer}"
        data = f"{circle.center_x},{circle.center_y},{circle.radius}"
        return f"{header}\n{data}"

    def format_arc(self, arc: Arc) -> str:
        """Format an arc entity to CSV format."""
        header = f"{arc.type},{arc.description},1,{arc.layer}"
        data = f"{arc.center_x},{arc.center_y},{arc.radius},{arc.start_angle},{arc.end_angle}"
        return f"{header}\n{data}"

    def format_polyline(self, polyline: Polyline) -> str:
        """Format a polyline entity to CSV format.

        Each vertex should be on its own line: x,y,start_width,end_width,bulge
        For basic polylines without width/bulge, we use 0,0,0 for those values.
        """
        header = f"{polyline.type},{polyline.description},1,{polyline.layer}"
        # Each point on its own line with sw, ew, bulge = 0, 0, 0
        vertex_lines = [f"{point.x},{point.y},0,0,0" for point in polyline.points]
        # If closed, append first point again
        if polyline.closed and len(polyline.points) > 0:
            first_point = polyline.points[0]
            vertex_lines.append(f"{first_point.x},{first_point.y},0,0,0")
        return f"{header}\n" + "\n".join(vertex_lines)

    def format_hatch(self, hatch: Hatch) -> str:
        """Format a hatch entity to CSV format.

        Each vertex: x,y,bulge (bulge=0 for straight edges)
        """
        header = f"{hatch.type},{hatch.description},1,{hatch.layer}"
        # Each point on its own line with bulge = 0
        vertex_lines = [f"{point.x},{point.y},0" for point in hatch.boundary_points]
        return f"{header}\n" + "\n".join(vertex_lines)

    def format_spline(self, spline: Spline) -> str:
        """
        Format a B-Spline entity to extended CSV format.

        Format: S, description, show_line, layer
                degree, num_control_points, num_fit_points, closed
                x1, y1, x2, y2, ... (control points)
                [fit_x1, fit_y1, ...] (fit points if present)
                [knot1, knot2, ...] (knots if present)
        """
        header = f"S,{spline.description},1,{spline.layer}"
        n_ctrl = len(spline.control_points)
        n_fit = len(spline.fit_points) if spline.fit_points else 0
        closed = 1 if spline.closed else 0

        meta = f"{spline.degree},{n_ctrl},{n_fit},{closed}"

        # Control points
        ctrl_coords = ",".join([f"{p.x},{p.y}" for p in spline.control_points])

        lines = [header, meta, ctrl_coords]

        # Fit points if present
        if spline.fit_points:
            fit_coords = ",".join([f"{p.x},{p.y}" for p in spline.fit_points])
            lines.append(fit_coords)

        # Knots if present
        if spline.knots:
            knot_str = ",".join([str(k) for k in spline.knots])
            lines.append(knot_str)

        return "\n".join(lines)

    def format_nurbs(self, nurbs: NURBSCurve) -> str:
        """
        Format a NURBS curve entity to extended CSV format.

        Format: N, description, show_line, layer
                degree, num_points, closed
                x1, y1, w1, x2, y2, w2, ... (weighted control points)
                [knot1, knot2, ...] (knots if present)
        """
        header = f"N,{nurbs.description},1,{nurbs.layer}"
        n_pts = len(nurbs.control_points)
        closed = 1 if nurbs.closed else 0

        meta = f"{nurbs.degree},{n_pts},{closed}"

        # Control points with weights
        pts_coords = ",".join([
            f"{p.x},{p.y},{p.weight}" for p in nurbs.control_points
        ])

        lines = [header, meta, pts_coords]

        # Knots if present
        if nurbs.knots:
            knot_str = ",".join([str(k) for k in nurbs.knots])
            lines.append(knot_str)

        return "\n".join(lines)

    def format_bezier(self, bezier: BezierCurve) -> str:
        """
        Format a Bezier curve entity to CSV format.

        Format: B, description, show_line, layer
                num_points (degree = num_points - 1)
                x1, y1, x2, y2, ... (control points)
        """
        header = f"B,{bezier.description},1,{bezier.layer}"
        n_pts = len(bezier.control_points)

        meta = f"{n_pts}"
        coords = ",".join([f"{p.x},{p.y}" for p in bezier.control_points])

        return f"{header}\n{meta}\n{coords}"

    def format_ellipse(self, ellipse: Ellipse) -> str:
        """
        Format an ellipse entity to CSV format.

        Format: E, description, show_line, layer
                center_x, center_y, major_x, major_y, ratio, start_param, end_param
        """
        header = f"E,{ellipse.description},1,{ellipse.layer}"
        data = (
            f"{ellipse.center_x},{ellipse.center_y},"
            f"{ellipse.major_axis_x},{ellipse.major_axis_y},"
            f"{ellipse.ratio},{ellipse.start_param},{ellipse.end_param}"
        )
        return f"{header}\n{data}"

    def format_polyline_with_curves(self, pw: PolylineWithCurves) -> str:
        """
        Format a polyline with curves (bulge) to CSV format.

        Format: PW, description, show_line, layer
                x1, y1, bulge1, sw1, ew1, x2, y2, bulge2, sw2, ew2, ...

        This is compatible with the standard polyline format but includes bulge.
        """
        header = f"P,{pw.description},1,{pw.layer}"

        # Format vertices with bulge and width
        vertex_data = []
        for v in pw.vertices:
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
            vertex_data.append(f"{x},{y},{sw},{ew},{bulge}")

        coords = "\n".join(vertex_data)
        return f"{header}\n{coords}"

    def format(self, entities: Union[ExtractedEntities, ExtendedEntities]) -> str:
        """Format all extracted entities to text_to_dxf CSV format."""
        output_lines = []

        # Format each type of entity
        for line in entities.lines:
            output_lines.append(self.format_line(line))

        for circle in entities.circles:
            output_lines.append(self.format_circle(circle))

        for arc in entities.arcs:
            output_lines.append(self.format_arc(arc))

        for polyline in entities.polylines:
            output_lines.append(self.format_polyline(polyline))

        for hatch in entities.hatches:
            output_lines.append(self.format_hatch(hatch))

        # Format curve entities if present (ExtendedEntities)
        if hasattr(entities, 'splines'):
            for spline in entities.splines:
                output_lines.append(self.format_spline(spline))

        if hasattr(entities, 'nurbs_curves'):
            for nurbs in entities.nurbs_curves:
                output_lines.append(self.format_nurbs(nurbs))

        if hasattr(entities, 'bezier_curves'):
            for bezier in entities.bezier_curves:
                output_lines.append(self.format_bezier(bezier))

        if hasattr(entities, 'ellipses'):
            for ellipse in entities.ellipses:
                output_lines.append(self.format_ellipse(ellipse))

        if hasattr(entities, 'polylines_with_curves'):
            for pw in entities.polylines_with_curves:
                output_lines.append(self.format_polyline_with_curves(pw))

        # Join with double newline separator (blank line between entities)
        return "\n\n".join(output_lines)

    def format_to_dict(self, entities: Union[ExtractedEntities, ExtendedEntities]) -> Dict[str, Any]:
        """Format entities as a dictionary for JSON responses."""
        result = {
            "lines": [line.model_dump() for line in entities.lines],
            "circles": [circle.model_dump() for circle in entities.circles],
            "arcs": [arc.model_dump() for arc in entities.arcs],
            "polylines": [polyline.model_dump() for polyline in entities.polylines],
            "hatches": [hatch.model_dump() for hatch in entities.hatches],
            "csv_format": self.format(entities),
            "notes": entities.notes
        }

        # Add curve entities if present
        if hasattr(entities, 'splines'):
            result["splines"] = [s.model_dump() for s in entities.splines]
        if hasattr(entities, 'nurbs_curves'):
            result["nurbs_curves"] = [n.model_dump() for n in entities.nurbs_curves]
        if hasattr(entities, 'bezier_curves'):
            result["bezier_curves"] = [b.model_dump() for b in entities.bezier_curves]
        if hasattr(entities, 'ellipses'):
            result["ellipses"] = [e.model_dump() for e in entities.ellipses]
        if hasattr(entities, 'polylines_with_curves'):
            result["polylines_with_curves"] = [pw.model_dump() for pw in entities.polylines_with_curves]

        return result
