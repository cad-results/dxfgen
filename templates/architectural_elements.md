# Standard Door - Interior
**Category**: architectural_element
**Description**: Standard interior door with swing arc

## Parameters
- door_width: 900 (Door width in mm)
- door_height: 2100 (Door height in mm)
- wall_thickness: 150 (Wall thickness in mm)
- swing_direction: inward (inward or outward)
- hinge_side: left (left or right when viewed from swing side)

## Prompt
Create a standard interior door representation with the following specifications:

- Door width: {door_width}mm
- Door height: {door_height}mm (for annotations)
- Wall thickness: {wall_thickness}mm
- Swing direction: {swing_direction}
- Hinge side: {hinge_side}
- Generate door opening as gap in wall (two parallel lines {wall_thickness}mm apart)
- Generate door swing arc: 90° arc from hinge point, radius = {door_width}mm
- Door frame marks at opening edges
- Layer: Doors
- Include annotation showing door size ({door_width}mm)

---

# Standard Door - Exterior
**Category**: architectural_element
**Description**: Exterior entrance door with threshold

## Parameters
- door_width: 1000 (Door width in mm)
- door_height: 2100 (Door height in mm)
- wall_thickness: 200 (Wall thickness in mm)
- double_door: false (Single or double door)
- swing_direction: inward (inward or outward)

## Prompt
Create an exterior entrance door with the following specifications:

- Door width: {door_width}mm (per panel if double)
- Door height: {door_height}mm
- Wall thickness: {wall_thickness}mm
- Double door: {double_door}
- Swing direction: {swing_direction}
- If double: Generate two door panels, each {door_width}mm, meeting at center
- Generate door opening gap in wall
- Generate swing arc(s) for each panel
- Threshold marked with line at bottom of opening
- Layer: Doors
- Include size annotation

---

# Standard Window
**Category**: architectural_element
**Description**: Standard residential window with frame

## Parameters
- window_width: 1200 (Window width in mm)
- window_height: 1200 (Window height in mm - shown in elevation)
- wall_thickness: 200 (Wall thickness in mm)
- sill_height: 900 (Height of window sill from floor in mm)
- window_type: fixed (fixed, sliding, or casement)

## Prompt
Create a standard window representation (plan view) with the following specifications:

- Window width: {window_width}mm
- Window height: {window_height}mm (noted in annotation)
- Wall thickness: {wall_thickness}mm
- Sill height: {sill_height}mm (noted in annotation)
- Window type: {window_type}
- Generate gap in wall for window opening ({window_width}mm)
- Frame representation: Short perpendicular lines at opening edges (100mm each side)
- If sliding: Show panel division with center line
- If casement: Show hinge side with small mark
- Layer: Windows
- Include annotation with size

---

# Straight Staircase
**Category**: architectural_element
**Description**: Straight run staircase with standard rise and run

## Parameters
- total_rise: 2700 (Total vertical rise in mm)
- num_steps: 14 (Number of steps/risers)
- tread_depth: 250 (Tread depth in mm)
- stair_width: 1000 (Staircase width in mm)
- direction: up (up or down from viewpoint)

## Prompt
Create a straight staircase representation (plan view) with the following specifications:

- Total rise: {total_rise}mm floor to floor
- Number of steps: {num_steps}
- Tread depth: {tread_depth}mm (going)
- Stair width: {stair_width}mm
- Direction arrow: {direction}
- Individual riser: {total_rise} / {num_steps} = calculated mm per step
- Generate {num_steps} parallel lines representing treads, spaced {tread_depth}mm apart
- Staircase outline: Rectangle {stair_width}mm wide × ({num_steps} × {tread_depth})mm long
- Direction arrow in center showing {direction}
- Handrails on both sides (lines parallel to stair edges, offset 50mm)
- Layer: Stairs
- Annotation: "{num_steps}R @ calculated rise"

---

# L-Shaped Staircase
**Category**: architectural_element
**Description**: L-shaped staircase with landing

## Parameters
- total_rise: 2700 (Total vertical rise in mm)
- num_steps_lower: 7 (Number of steps in lower flight)
- num_steps_upper: 7 (Number of steps in upper flight)
- tread_depth: 250 (Tread depth in mm)
- stair_width: 1000 (Staircase width in mm)
- landing_size: 1000 (Landing square dimension in mm)

## Prompt
Create an L-shaped staircase with landing (plan view) with the following specifications:

- Total rise: {total_rise}mm
- Lower flight: {num_steps_lower} steps going one direction
- Upper flight: {num_steps_upper} steps at 90° turn
- Landing: {landing_size}mm × {landing_size}mm at turn
- Tread depth: {tread_depth}mm
- Stair width: {stair_width}mm
- Generate lower flight: {num_steps_lower} treads
- Generate landing square at top of lower flight
- Generate upper flight: {num_steps_upper} treads perpendicular to lower
- Direction arrows showing up path
- Handrails around perimeter
- Layer: Stairs
- Annotations showing step counts

---

# Kitchen Counter
**Category**: architectural_element
**Description**: Standard kitchen counter with base cabinets

## Parameters
- counter_length: 3000 (Counter length in mm)
- counter_depth: 600 (Counter depth in mm)
- include_sink: true (Include sink in counter)
- sink_position: center (left, center, or right)
- include_appliances: false (Show appliance outlines)

## Prompt
Create a kitchen counter representation (plan view) with the following specifications:

- Counter length: {counter_length}mm
- Counter depth: {counter_depth}mm (standard depth)
- Include sink: {include_sink}
- If sink included:
  - Position: {sink_position}
  - Sink size: 500mm × 400mm rectangle
- Include appliances: {include_appliances}
- Counter as rectangle {counter_length}mm × {counter_depth}mm
- Base cabinet represented by double line showing cabinet doors
- Layer: Furniture or Fixtures
- If sink, show oval or rectangle at specified position

---

# Bathroom Fixtures Set
**Category**: architectural_element
**Description**: Standard bathroom fixture set (toilet, sink, shower/tub)

## Parameters
- include_toilet: true (Include toilet)
- include_sink: true (Include sink/vanity)
- include_shower: true (Include shower stall)
- include_tub: false (Include bathtub instead of/in addition to shower)
- vanity_width: 600 (Vanity/sink width in mm)

## Prompt
Create bathroom fixtures with the following specifications:

- Toilet: {include_toilet} - if true, generate 700mm × 400mm rectangle (tank and bowl)
- Sink/Vanity: {include_sink} - if true, generate {vanity_width}mm × 500mm rectangle with oval sink
- Shower: {include_shower} - if true, generate 900mm × 900mm square with drain mark
- Bathtub: {include_tub} - if true, generate 1700mm × 700mm rectangle (standard tub)
- All fixtures as plan view representations
- Layer: Fixtures
- Space fixtures appropriately for typical bathroom layout
- Toilet: positioned with clearance space
- Vanity: typically along wall
- Shower/tub: in corner or along wall

---

# Dining Table
**Category**: architectural_element
**Description**: Dining table with chairs

## Parameters
- table_shape: rectangular (rectangular or round)
- table_length: 1800 (Table length in mm if rectangular)
- table_width: 900 (Table width in mm if rectangular)
- table_diameter: 1200 (Table diameter in mm if round)
- num_chairs: 6 (Number of chairs around table)
- show_chairs: true (Show chair positions)

## Prompt
Create a dining table with chairs (plan view) with the following specifications:

- Table shape: {table_shape}
- If rectangular: {table_length}mm × {table_width}mm
- If round: {table_diameter}mm diameter
- Number of chairs: {num_chairs}
- Show chairs: {show_chairs}
- Generate table outline (rectangle or circle)
- If chairs shown: Generate chair positions around table
  - Chair size: 450mm × 450mm squares
  - Space evenly: {num_chairs} chairs around perimeter
  - Chairs set back 100-200mm from table edge
- Layer: Furniture
- Clean, simple representation

---

# Bed
**Category**: architectural_element
**Description**: Bed with headboard indication

## Parameters
- bed_size: double (single, double, queen, or king)
- headboard_side: north (north, south, east, west - which wall)
- include_nightstands: true (Include bedside tables)

## Prompt
Create a bed representation (plan view) with the following specifications:

- Bed size: {bed_size}
  - Single: 1000mm × 2000mm
  - Double: 1400mm × 2000mm
  - Queen: 1600mm × 2000mm
  - King: 2000mm × 2000mm
- Headboard side: {headboard_side} (which wall the head is against)
- Include nightstands: {include_nightstands}
- Generate bed rectangle at appropriate size
- Show mattress outline
- Show pillow area (smaller rectangle at headboard end, 20% of length)
- Headboard indicated by thicker line or double line at head end
- If nightstands: Generate 500mm × 400mm rectangles on both sides at headboard
- Layer: Furniture
- Proper orientation with head against specified wall

---

# Sofa - 3-Seater
**Category**: architectural_element
**Description**: Three-seat sofa for living room

## Parameters
- sofa_length: 2000 (Sofa length in mm)
- sofa_depth: 900 (Sofa depth in mm)
- sofa_style: standard (standard, sectional-left, sectional-right)
- show_cushions: true (Show cushion divisions)

## Prompt
Create a sofa representation (plan view) with the following specifications:

- Length: {sofa_length}mm (3-seat standard)
- Depth: {sofa_depth}mm
- Style: {sofa_style}
- Show cushions: {show_cushions}
- Generate sofa rectangle {sofa_length}mm × {sofa_depth}mm
- If standard: Simple rectangle with back and arms indicated
- If sectional: L-shape with extended chaise on specified side
- If cushions shown: Divide into 3 equal sections with lines
- Back of sofa indicated by thicker line on one side
- Arms shown as small rectangles at ends
- Layer: Furniture

---

# Desk with Chair
**Category**: architectural_element
**Description**: Work desk with office chair

## Parameters
- desk_length: 1400 (Desk length in mm)
- desk_depth: 700 (Desk depth in mm)
- include_drawers: true (Show drawer unit)
- chair_position: front (front or side - where chair sits)

## Prompt
Create a desk with chair (plan view) with the following specifications:

- Desk length: {desk_length}mm
- Desk depth: {desk_depth}mm
- Include drawers: {include_drawers}
- Chair position: {chair_position}
- Generate desk rectangle {desk_length}mm × {desk_depth}mm
- If drawers: Show drawer unit (400mm × {desk_depth}mm) on one side
- Generate chair: 600mm × 600mm square at specified position
- Chair positioned for ergonomic use (set back from desk edge)
- Layer: Furniture
