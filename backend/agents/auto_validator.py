"""Auto-Validator Agent - Enhanced validation with automatic fixes."""

from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from .entity_extractor import ExtractedEntities, Line, Circle, Arc, Polyline, Hatch, Point
import math


class AutoFix(BaseModel):
    """Represents an automatic fix that was applied."""

    fix_type: str = Field(description="Type of fix applied")
    description: str = Field(description="Description of what was fixed")
    before: str = Field(description="State before fix")
    after: str = Field(description="State after fix")
    severity: str = Field(description="Severity: 'minor', 'moderate', 'critical'")


class ValidationResult(BaseModel):
    """Enhanced validation result with auto-fixes."""

    is_valid: bool = Field(description="Whether the metadata is valid and ready for DXF generation")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0")
    issues: List[str] = Field(default_factory=list, description="List of issues found (not auto-fixed)")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    auto_fixes_applied: List[AutoFix] = Field(default_factory=list, description="List of automatic fixes applied")
    questions_for_user: List[str] = Field(default_factory=list, description="Questions to ask the user for clarification")
    summary: str = Field(description="Summary of the validation")


class AutoValidatorAgent:
    """
    Enhanced validator agent with automatic fix capabilities.

    Can automatically fix common issues when auto_accept mode is enabled:
    - Duplicate points in polylines/hatches
    - Unclosed polylines that should be closed
    - Angle normalization (0-360°)
    - Unrealistic scales/dimensions
    - Layer assignments
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert CAD quality assurance specialist with automatic fix capabilities.

Your job is to validate DXF metadata and, when auto-accept mode is enabled, automatically fix common issues.

**Validation Checks:**

1. **Completeness**: Are all entities properly defined with required parameters?
2. **Correctness**: Do coordinates and measurements make sense?
3. **Consistency**: Do entities relate to each other logically?
4. **Quality**: Is the description clear? Are layers properly assigned?
5. **Format compliance**: Does it match text_to_dxf requirements?

**Auto-Fixable Issues** (when auto_accept = True):

1. **Duplicate Points**:
   - Issue: Polylines/hatches with consecutive identical points
   - Fix: Remove duplicates automatically
   - Severity: Minor

2. **Geometric Corrections**:
   - Issue: Polylines that should be closed but aren't (first != last point)
   - Fix: Add first point to end if distance < 1mm
   - Issue: Angles outside 0-360° range
   - Fix: Normalize to 0-360°
   - Issue: Negative radii
   - Fix: Convert to absolute value
   - Issue: Zero-length lines (start point == end point)
   - Fix: For window frames, apply standard 1200mm dimension; for others, remove
   - Severity: Minor to Moderate

3. **Layer Assignments**:
   - Issue: All entities on layer "0" or inconsistent layers
   - Fix: Assign logical layers based on entity type and description
     - Walls → "Walls" layer
     - Doors → "Doors" layer
     - Windows → "Windows" layer
     - Furniture → "Furniture" layer
     - Gears, mechanical → "Outlines" layer
   - Severity: Minor

4. **Scale/Unit Issues**:
   - Issue: Unrealistic dimensions (e.g., 1mm thick walls, 10m diameter gears)
   - Fix: Apply scale correction based on context
     - Architectural walls < 100mm → multiply by 100 (likely cm input treated as mm)
     - Mechanical parts > 1000mm → divide by 10 (likely wrong unit)
   - Severity: Moderate to Critical

**Process:**

1. Analyze the entities and formatted metadata
2. Identify all issues (both fixable and non-fixable)
3. If auto_accept = True:
   - Automatically apply fixes for standard issues
   - Log each fix in auto_fixes_applied
   - Only report truly ambiguous issues in questions_for_user
4. If auto_accept = False:
   - Report all issues
   - Ask user for confirmation on fixes

**Professional Dimension Standards** (for scale validation):
- Residential walls: 150-200mm thick
- Doors: 800-1000mm wide
- Windows: 900-1800mm wide
- Rooms: 2000-8000mm dimensions
- Gears: 10-500mm diameter typical
- Bearings: 10-200mm diameter typical
- Bolts: 3-30mm diameter

**Output:**

- Mark is_valid = True if no critical issues remain after auto-fixes
- Set confidence_score based on remaining uncertainties
- In auto_fixes_applied, document every automatic change
- In issues, list only problems that need user attention
- In questions_for_user, ask only truly ambiguous questions

**Example Auto-Fix Log:**

```json
{{
  "fix_type": "duplicate_points",
  "description": "Removed 3 duplicate consecutive points from polyline 'Room Wall'",
  "before": "Polyline with 12 points including duplicates",
  "after": "Polyline with 9 unique points",
  "severity": "minor"
}}
```

Be thorough, apply fixes intelligently, and maintain high quality standards."""),
            ("user", """Original User Input:
{user_input}

Extracted Entities:
{entities}

Formatted CSV Metadata:
{formatted_csv}

Auto-Accept Mode: {auto_accept}

Please validate this metadata and apply automatic fixes if auto-accept is enabled.""")
        ])

    def validate(
        self,
        user_input: str,
        entities: Dict[str, Any],
        formatted_csv: str,
        auto_accept: bool = False
    ) -> Tuple[ValidationResult, ExtractedEntities]:
        """
        Validate the extracted entities and formatted metadata.

        Args:
            user_input: Original user input
            entities: Extracted entities as dict
            formatted_csv: Formatted CSV metadata
            auto_accept: Whether to automatically apply fixes

        Returns:
            Tuple of (ValidationResult, potentially modified ExtractedEntities)
        """
        # First, perform LLM-based validation
        structured_llm = self.llm.with_structured_output(ValidationResult)
        chain = self.prompt | structured_llm

        validation_result = chain.invoke({
            "user_input": user_input,
            "entities": str(entities),
            "formatted_csv": formatted_csv,
            "auto_accept": auto_accept
        })

        # If auto_accept, also apply programmatic fixes
        if auto_accept:
            from .entity_extractor import ExtractedEntities
            entities_obj = ExtractedEntities(**entities)
            fixed_entities, programmatic_fixes = self._apply_programmatic_fixes(entities_obj)

            # Merge programmatic fixes into validation result
            validation_result.auto_fixes_applied.extend(programmatic_fixes)

            return validation_result, fixed_entities
        else:
            from .entity_extractor import ExtractedEntities
            return validation_result, ExtractedEntities(**entities)

    def _apply_programmatic_fixes(self, entities: ExtractedEntities) -> Tuple[ExtractedEntities, List[AutoFix]]:
        """
        Apply programmatic fixes to entities.

        Returns:
            Tuple of (fixed entities, list of fixes applied)
        """
        fixes = []

        # Fix 1: Remove duplicate points in polylines
        for i, polyline in enumerate(entities.polylines):
            original_count = len(polyline.points)
            unique_points = []
            prev_point = None

            for point in polyline.points:
                if prev_point is None or not self._points_equal(point, prev_point):
                    unique_points.append(point)
                    prev_point = point

            if len(unique_points) < original_count:
                polyline.points = unique_points
                fixes.append(AutoFix(
                    fix_type="duplicate_points",
                    description=f"Removed {original_count - len(unique_points)} duplicate points from polyline '{polyline.description}'",
                    before=f"{original_count} points",
                    after=f"{len(unique_points)} unique points",
                    severity="minor"
                ))

        # Fix 2: Remove duplicate points in hatches
        for i, hatch in enumerate(entities.hatches):
            original_count = len(hatch.boundary_points)
            unique_points = []
            prev_point = None

            for point in hatch.boundary_points:
                if prev_point is None or not self._points_equal(point, prev_point):
                    unique_points.append(point)
                    prev_point = point

            if len(unique_points) < original_count:
                hatch.boundary_points = unique_points
                fixes.append(AutoFix(
                    fix_type="duplicate_points",
                    description=f"Removed {original_count - len(unique_points)} duplicate points from hatch '{hatch.description}'",
                    before=f"{original_count} points",
                    after=f"{len(unique_points)} unique points",
                    severity="minor"
                ))

        # Fix 3: Close polylines that should be closed
        for polyline in entities.polylines:
            if len(polyline.points) >= 3 and not polyline.closed:
                first = polyline.points[0]
                last = polyline.points[-1]
                distance = math.sqrt((first.x - last.x)**2 + (first.y - last.y)**2)

                # If first and last points are very close (< 1mm), close the polyline
                if distance < 1.0 and distance > 0.01:
                    polyline.closed = True
                    fixes.append(AutoFix(
                        fix_type="close_polyline",
                        description=f"Closed polyline '{polyline.description}' (gap was {distance:.2f}mm)",
                        before="Open polyline",
                        after="Closed polyline",
                        severity="minor"
                    ))

        # Fix 4: Normalize arc angles
        for arc in entities.arcs:
            original_start = arc.start_angle
            original_end = arc.end_angle

            # Normalize to 0-360 range
            arc.start_angle = arc.start_angle % 360.0
            arc.end_angle = arc.end_angle % 360.0

            if original_start != arc.start_angle or original_end != arc.end_angle:
                fixes.append(AutoFix(
                    fix_type="normalize_angles",
                    description=f"Normalized arc angles for '{arc.description}'",
                    before=f"{original_start}° to {original_end}°",
                    after=f"{arc.start_angle}° to {arc.end_angle}°",
                    severity="minor"
                ))

        # Fix 5: Fix negative radii
        for circle in entities.circles:
            if circle.radius < 0:
                circle.radius = abs(circle.radius)
                fixes.append(AutoFix(
                    fix_type="fix_negative_radius",
                    description=f"Fixed negative radius for circle '{circle.description}'",
                    before=f"{-circle.radius}mm",
                    after=f"{circle.radius}mm",
                    severity="moderate"
                ))

        for arc in entities.arcs:
            if arc.radius < 0:
                arc.radius = abs(arc.radius)
                fixes.append(AutoFix(
                    fix_type="fix_negative_radius",
                    description=f"Fixed negative radius for arc '{arc.description}'",
                    before=f"{-arc.radius}mm",
                    after=f"{arc.radius}mm",
                    severity="moderate"
                ))

        # Fix 6: Detect and fix zero-length lines (e.g., window frames with same start/end)
        lines_to_remove = []
        for i, line in enumerate(entities.lines):
            distance = math.sqrt((line.x2 - line.x1)**2 + (line.y2 - line.y1)**2)

            # If line has zero or near-zero length, try to fix or remove
            if distance < 0.01:
                # Check if it's a window frame - give it standard dimensions
                if any(kw in line.description.lower() for kw in ["window", "frame", "glazing"]):
                    # Create a horizontal or vertical window frame with standard 1200mm width
                    # Determine orientation from description or default to horizontal
                    if "vertical" in line.description.lower():
                        line.y2 = line.y1 + 1200.0  # 1200mm vertical window
                    else:
                        line.x2 = line.x1 + 1200.0  # 1200mm horizontal window

                    fixes.append(AutoFix(
                        fix_type="fix_zero_length_line",
                        description=f"Fixed zero-length window frame '{line.description}' by setting standard 1200mm dimension",
                        before=f"Line from ({line.x1:.1f}, {line.y1:.1f}) to ({line.x1:.1f}, {line.y1:.1f})",
                        after=f"Line from ({line.x1:.1f}, {line.y1:.1f}) to ({line.x2:.1f}, {line.y2:.1f})",
                        severity="moderate"
                    ))
                else:
                    # For other zero-length lines, mark for removal
                    lines_to_remove.append(i)
                    fixes.append(AutoFix(
                        fix_type="remove_zero_length_line",
                        description=f"Removed zero-length line '{line.description}'",
                        before=f"Line at ({line.x1:.1f}, {line.y1:.1f})",
                        after="Removed",
                        severity="minor"
                    ))

        # Remove marked lines
        for i in reversed(lines_to_remove):
            del entities.lines[i]

        # Fix 7: Auto-assign layers based on description keywords
        layer_keywords = {
            "Walls": ["wall", "exterior", "interior"],
            "Doors": ["door", "swing", "entrance"],
            "Windows": ["window", "glazing"],
            "Furniture": ["bed", "table", "chair", "sofa", "desk", "furniture"],
            "Fixtures": ["toilet", "sink", "shower", "bath"],
            "Outlines": ["gear", "bearing", "shaft", "bolt"]
        }

        # Check and fix lines
        for line in entities.lines:
            if line.layer == "0":
                for layer_name, keywords in layer_keywords.items():
                    if any(kw in line.description.lower() for kw in keywords):
                        line.layer = layer_name
                        fixes.append(AutoFix(
                            fix_type="assign_layer",
                            description=f"Assigned layer '{layer_name}' to line '{line.description}'",
                            before="Layer '0'",
                            after=f"Layer '{layer_name}'",
                            severity="minor"
                        ))
                        break

        # Similar for other entity types
        for polyline in entities.polylines:
            if polyline.layer == "0":
                for layer_name, keywords in layer_keywords.items():
                    if any(kw in polyline.description.lower() for kw in keywords):
                        polyline.layer = layer_name
                        fixes.append(AutoFix(
                            fix_type="assign_layer",
                            description=f"Assigned layer '{layer_name}' to polyline '{polyline.description}'",
                            before="Layer '0'",
                            after=f"Layer '{layer_name}'",
                            severity="minor"
                        ))
                        break

        for circle in entities.circles:
            if circle.layer == "0":
                for layer_name, keywords in layer_keywords.items():
                    if any(kw in circle.description.lower() for kw in keywords):
                        circle.layer = layer_name
                        fixes.append(AutoFix(
                            fix_type="assign_layer",
                            description=f"Assigned layer '{layer_name}' to circle '{circle.description}'",
                            before="Layer '0'",
                            after=f"Layer '{layer_name}'",
                            severity="minor"
                        ))
                        break

        for arc in entities.arcs:
            if arc.layer == "0":
                for layer_name, keywords in layer_keywords.items():
                    if any(kw in arc.description.lower() for kw in keywords):
                        arc.layer = layer_name
                        fixes.append(AutoFix(
                            fix_type="assign_layer",
                            description=f"Assigned layer '{layer_name}' to arc '{arc.description}'",
                            before="Layer '0'",
                            after=f"Layer '{layer_name}'",
                            severity="minor"
                        ))
                        break

        # Fix 8: Shift coordinates if any are negative to ensure all are >= 0
        min_x = float('inf')
        min_y = float('inf')

        # Find minimum coordinates across all entities
        for line in entities.lines:
            min_x = min(min_x, line.x1, line.x2)
            min_y = min(min_y, line.y1, line.y2)
        for circle in entities.circles:
            min_x = min(min_x, circle.center_x - circle.radius)
            min_y = min(min_y, circle.center_y - circle.radius)
        for arc in entities.arcs:
            min_x = min(min_x, arc.center_x - arc.radius)
            min_y = min(min_y, arc.center_y - arc.radius)
        for polyline in entities.polylines:
            for point in polyline.points:
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)
        for hatch in entities.hatches:
            for point in hatch.boundary_points:
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)

        # If minimum is negative, shift all coordinates
        if min_x != float('inf') and min_y != float('inf') and (min_x < 0 or min_y < 0):
            shift_x = -min_x if min_x < 0 else 0
            shift_y = -min_y if min_y < 0 else 0

            # Apply shift to all entities
            for line in entities.lines:
                line.x1 += shift_x
                line.x2 += shift_x
                line.y1 += shift_y
                line.y2 += shift_y
            for circle in entities.circles:
                circle.center_x += shift_x
                circle.center_y += shift_y
            for arc in entities.arcs:
                arc.center_x += shift_x
                arc.center_y += shift_y
            for polyline in entities.polylines:
                for point in polyline.points:
                    point.x += shift_x
                    point.y += shift_y
            for hatch in entities.hatches:
                for point in hatch.boundary_points:
                    point.x += shift_x
                    point.y += shift_y

            fixes.append(AutoFix(
                fix_type="coordinate_shift",
                description=f"Shifted all coordinates by ({shift_x:.1f}, {shift_y:.1f}) to ensure non-negative values",
                before=f"Min coordinates: ({min_x:.1f}, {min_y:.1f})",
                after="Min coordinates: (0, 0)",
                severity="minor"
            ))

        return entities, fixes

    @staticmethod
    def _points_equal(p1: Point, p2: Point, tolerance: float = 0.01) -> bool:
        """Check if two points are equal within tolerance."""
        return abs(p1.x - p2.x) < tolerance and abs(p1.y - p2.y) < tolerance

    def quick_validate(self, formatted_csv: str) -> bool:
        """Perform a quick syntax validation without LLM."""
        if not formatted_csv or formatted_csv.strip() == "":
            return False

        lines = formatted_csv.strip().split('\n')
        if len(lines) < 2:  # Need at least header and data
            return False

        # Basic format checking
        for i in range(0, len(lines), 3):  # Each entity is 3 lines (header, data, empty)
            if i >= len(lines):
                break
            header = lines[i].strip()
            if not (header.startswith('[') and header.endswith(']')):
                continue  # Skip if not a header
            if i + 1 < len(lines):
                data = lines[i + 1].strip()
                if not data:
                    return False

        return True
