"""Detail Refinement Agent - Recursively refines vague queries into detailed specifications."""

from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class RefinedSpecification(BaseModel):
    """Detailed specification after refinement."""

    is_detailed_enough: bool = Field(
        description="Whether the specification is detailed enough for entity extraction"
    )
    confidence_score: float = Field(
        description="Confidence that all ambiguities have been resolved (0.0 to 1.0)"
    )
    refined_description: str = Field(
        description="The fully detailed, unambiguous description"
    )
    key_specifications: List[str] = Field(
        description="List of key specifications extracted (dimensions, quantities, arrangements)"
    )
    domain: str = Field(
        description="Identified domain (architectural, mechanical, furniture, etc.)"
    )
    missing_details: List[str] = Field(
        description="Details still missing or ambiguous (empty list if none)"
    )
    suggested_defaults: List[str] = Field(
        description="Suggested default values as key=value strings (e.g., ['num_bedrooms=3', 'total_area_m2=150'])"
    )
    refinement_notes: str = Field(
        description="Notes about the refinement process"
    )


class DetailRefinementAgent:
    """Agent that recursively refines vague queries into detailed specifications."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert specification analyst who transforms vague descriptions into detailed, unambiguous specifications for CAD drawing generation.

Your job is to take ANY description - no matter how vague - and refine it into concrete, actionable specifications.

**Refinement Process:**

1. **Identify Domain & Context**:
   - Architectural: floor plans, buildings, rooms, houses, offices
   - Mechanical: gears, parts, machines, assemblies, fasteners
   - Furniture: chairs, tables, beds, cabinets
   - Abstract/Creative: patterns, designs, artistic layouts
   - Infrastructure: roads, networks, utilities

2. **Break Down Vague Terms**:
   - "big house" → How many bedrooms? Square footage? Single/multi-story? Style?
   - "gear" → How many teeth? Pitch diameter? Pressure angle? Module?
   - "castle" → Defensive structure with towers? Courtyard? Moat? Number of buildings?
   - "road network" → How many roads? Intersections? Width? Pattern (grid, radial)?
   - "table" → Dining, coffee, desk? Dimensions? Shape (rectangular, round)?

3. **Apply Professional Standards & Common Practices**:

   **Architectural Defaults:**
   - Residential room: 3m × 3m to 5m × 4m
   - Door width: 900mm (interior), 1000mm (exterior)
   - Door height: 2100mm
   - Window: 1200mm × 1200mm typical
   - Wall thickness: 150mm (interior), 200mm (exterior)
   - Ceiling height: 2700mm (residential), 3000mm (commercial)
   - Bedroom: 3m × 3.5m minimum
   - Bathroom: 2m × 2m minimum
   - Kitchen: 3m × 3m minimum
   - Living room: 4m × 5m typical

   **Mechanical Engineering Defaults:**
   - Small gear: 20-30mm diameter, 12-20 teeth
   - Medium gear: 50-100mm diameter, 25-50 teeth
   - Large gear: 150mm+ diameter, 60+ teeth
   - Standard pressure angle: 20°
   - Bolt head: M8 = 13mm wrench, M10 = 17mm wrench
   - Bearing: Inner diameter based on shaft size

   **Furniture Defaults:**
   - Dining table: 1800mm × 900mm × 750mm (6 person)
   - Coffee table: 1200mm × 600mm × 450mm
   - Single bed: 1000mm × 2000mm
   - Double bed: 1400mm × 2000mm
   - King bed: 2000mm × 2000mm
   - Desk: 1400mm × 700mm × 750mm
   - Chair seat height: 450mm
   - Sofa: 2000mm × 900mm × 850mm (3-seater)

4. **Specify Quantities & Arrangements**:
   - "rooms" → How many? What types? How arranged (linear, grid, clustered)?
   - "scattered chambers" → How many? Random or evenly distributed? Bounds?
   - "teeth on gear" → How many? Evenly spaced (360°/n)?
   - "windows" → How many per wall? Centered or distributed?

5. **Define Spatial Relationships**:
   - Room adjacencies (bedroom next to bathroom, kitchen near dining)
   - Door positions (centered in wall, offset to corner)
   - Furniture placement (couch against wall, table centered)
   - Component connections (pipes connecting to valves, gears meshing)

6. **Establish Scale & Units**:
   - Architectural: meters (m) or millimeters (mm)
   - Mechanical: millimeters (mm)
   - Large infrastructure: meters (m)
   - Ensure consistency

7. **Fill Knowledge Gaps with Reasoning**:
   - "big house" → Assume 3-4 bedrooms, 150-200m² typical
   - "castle layout" → Assume medieval style: outer walls, courtyard, towers at corners, great hall
   - "office" → Assume open plan or cubicle layout, 3m²-5m² per person
   - "warehouse" → Large open space (20m × 30m+), loading dock, office area

**Output Requirements:**

- Mark `is_detailed_enough = True` ONLY if:
  - ALL dimensions are specified or defaulted
  - ALL quantities are known
  - ALL spatial relationships are clear
  - NO ambiguities remain

- Provide `confidence_score`:
  - 1.0 = Fully specified, zero ambiguity
  - 0.8-0.9 = Minor assumptions made with strong defaults
  - 0.6-0.7 = Some assumptions required
  - <0.6 = Still vague, needs more refinement

- In `key_specifications`, list concrete details:
  - "3-bedroom house: 150m² total area"
  - "Master bedroom: 4m × 3.5m, located northeast"
  - "Bedroom 2: 3m × 3m, located northwest"
  - "Living room: 5m × 4m, southern exposure"
  - "Kitchen: 3m × 3m, adjacent to dining"
  - "2 bathrooms: 2m × 2m each"
  - "Front door: 1000mm wide, south wall"
  - "Windows: 1200mm × 1200mm, one per exterior wall in each room"

- In `suggested_defaults`, provide reasonable values as key=value strings:
  [
    "total_area_m2=150",
    "num_bedrooms=3",
    "num_bathrooms=2",
    "floor_count=1",
    "wall_thickness_mm=200",
    "door_width_mm=900",
    "window_size_mm=1200x1200",
    "ceiling_height_mm=2700"
  ]

**Examples:**

Input: "build a big house"
Output:
- is_detailed_enough: False (first pass)
- confidence_score: 0.3
- refined_description: "A residential house, but specific room count, layout, and dimensions not specified"
- missing_details: ["number of bedrooms", "number of bathrooms", "total area", "single or multi-story", "room arrangement"]
- suggested_defaults: ["num_bedrooms=3", "num_bathrooms=2", "total_area_m2=150", "floor_count=1"]

After Pass 2 (with defaults applied):
- is_detailed_enough: True
- confidence_score: 0.85
- refined_description: "Single-story residential house with 3 bedrooms (master: 4m×3.5m, bedroom2: 3m×3m, bedroom3: 3m×3m), 2 bathrooms (2m×2m each), living room (5m×4m), kitchen (3m×3m), dining area (3m×3m), entrance hallway (2m×4m). Total area approximately 150m². Walls 200mm thick, standard doors 900mm wide, windows 1200mm×1200mm. Room arrangement: entrance to hallway, living room center, kitchen and dining adjacent, bedrooms along one side with bathrooms."
- key_specifications: ["3 bedrooms: 4m×3.5m (master), 3m×3m (br2), 3m×3m (br3)", "2 bathrooms: 2m×2m each", ...]

Be thorough, logical, and apply professional standards. Transform vague ideas into concrete specifications."""),
            ("user", """Original Input: {user_input}

Current Refinement Pass: {pass_number} of {max_passes}

Previous Refinement (if any): {previous_refinement}

Please analyze and refine this description. If this is not the first pass, build upon the previous refinement by applying suggested defaults and filling remaining gaps.""")
        ])

    def refine(
        self,
        user_input: str,
        pass_number: int = 1,
        max_passes: int = 3,
        previous_refinement: Optional[str] = None
    ) -> RefinedSpecification:
        """Refine the user input to add more detail."""
        structured_llm = self.llm.with_structured_output(RefinedSpecification)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "user_input": user_input,
            "pass_number": pass_number,
            "max_passes": max_passes,
            "previous_refinement": previous_refinement or "None (first pass)"
        })

        return result

    def refine_recursively(
        self,
        user_input: str,
        max_passes: int = 3,
        auto_accept: bool = False
    ) -> RefinedSpecification:
        """
        Recursively refine until detailed enough or max passes reached.

        Args:
            user_input: The vague or incomplete user description
            max_passes: Maximum number of refinement passes (default 3)
            auto_accept: If True, automatically apply suggested defaults without user input

        Returns:
            Final refined specification
        """
        current_refinement = None
        result = None

        for pass_num in range(1, max_passes + 1):
            result = self.refine(
                user_input=user_input,
                pass_number=pass_num,
                max_passes=max_passes,
                previous_refinement=current_refinement
            )

            # If detailed enough and confident, stop
            if result.is_detailed_enough and result.confidence_score >= 0.75:
                break

            # Prepare for next pass by applying defaults
            if pass_num < max_passes:
                current_refinement = result.refined_description

                # In auto-accept mode, automatically apply suggested defaults
                if auto_accept and result.suggested_defaults:
                    defaults_text = ", ".join(result.suggested_defaults)
                    current_refinement += f"\n\nApplied defaults: {defaults_text}"

        return result
