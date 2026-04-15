# Spur Gear - Small
**Category**: mechanical
**Description**: Small spur gear for light-duty applications

## Parameters
- num_teeth: 20 (Number of gear teeth)
- module: 2 (Gear module in mm - determines tooth size)
- bore_diameter: 10 (Center bore diameter in mm)
- include_keyway: false (Include keyway slot in bore)

## Prompt
Create a professional spur gear with the following specifications:

- Number of teeth: {num_teeth}
- Module: {module}mm
- Calculated pitch diameter: {module} × {num_teeth} = {calculated_pd}mm
- Calculated outer diameter: {module} × ({num_teeth} + 2) = {calculated_od}mm
- Calculated root diameter: {module} × ({num_teeth} - 2.5) = {calculated_rd}mm
- Bore diameter: {bore_diameter}mm
- Include keyway: {include_keyway}
- Pressure angle: 20° (standard)
- Generate tooth profiles: Simple radial lines or trapezoids at proper spacing
- Layer organization: Outlines, CenterLines
- Include center lines (horizontal and vertical through center)

Generate complete gear with all circles (outer, pitch, root, bore) and tooth representations.

---

# Spur Gear - Medium
**Category**: mechanical
**Description**: Medium spur gear for general applications

## Parameters
- num_teeth: 40 (Number of gear teeth)
- module: 3 (Gear module in mm)
- bore_diameter: 25 (Center bore diameter in mm)
- include_keyway: true (Include keyway slot)
- keyway_width: 8 (Keyway width in mm)

## Prompt
Create a professional medium spur gear with the following specifications:

- Number of teeth: {num_teeth}
- Module: {module}mm
- Pitch diameter: {module} × {num_teeth}mm
- Outer diameter: {module} × ({num_teeth} + 2)mm
- Root diameter: {module} × ({num_teeth} - 2.5)mm
- Bore diameter: {bore_diameter}mm
- Keyway: {include_keyway} - if true, {keyway_width}mm wide rectangular slot from bore to outer edge
- Tooth spacing: 360° / {num_teeth}
- Pressure angle: 20°
- Layer organization: Outlines, CenterLines, Keyway (if included)
- Include engineering annotations with critical dimensions

---

# Ball Bearing
**Category**: mechanical
**Description**: Deep groove ball bearing standard representation

## Parameters
- bearing_series: 6205 (Standard bearing designation)
- bore_diameter: 25 (Inner diameter in mm)
- outer_diameter: 52 (Outer diameter in mm)
- width: 15 (Bearing width in mm)

## Prompt
Create a professional ball bearing representation (section view) with the following specifications:

- Bearing designation: {bearing_series}
- Bore diameter (inner race): {bore_diameter}mm
- Outer diameter (outer race): {outer_diameter}mm
- Width: {width}mm
- Ball pitch diameter: ({outer_diameter} + {bore_diameter}) / 2 (approximate)
- Generate concentric circles:
  - Outer race circle at OD
  - Inner race circle at bore
  - Ball pitch circle at mid-point
- Layer organization: Outlines, CenterLines
- Include center lines and dimension annotations
- Section view showing cross-section

---

# Hex Bolt
**Category**: mechanical
**Description**: ISO metric hex head bolt

## Parameters
- bolt_size: M8 (Metric bolt size: M3, M4, M5, M6, M8, M10, M12)
- length: 40 (Total length in mm including head)
- head_type: hex (hex or socket)

## Prompt
Create a professional hex bolt drawing with the following specifications:

- Bolt size: {bolt_size}
- Thread nominal diameter: Extract number from {bolt_size} (e.g., M8 = 8mm)
- Length: {length}mm (including head)
- Head type: {head_type}
- If M8: hex head 13mm across flats, 5.5mm height
- If M6: hex head 10mm across flats, 4mm height
- If M10: hex head 17mm across flats, 7mm height
- Generate hexagonal head (6-point closed polyline)
- Generate shank as circle (top view) or rectangle (side view)
- Thread representation: Simplified parallel lines
- Layer organization: Outlines, CenterLines, Threads
- Include dimension annotations

---

# Shaft with Keyway
**Category**: mechanical
**Description**: Precision shaft with keyway for power transmission

## Parameters
- shaft_diameter: 20 (Shaft diameter in mm)
- shaft_length: 100 (Total shaft length in mm)
- keyway_width: 6 (Keyway width in mm)
- keyway_depth: 3.5 (Keyway depth in mm)
- include_shoulder: false (Include shoulder/step in diameter)
- shoulder_diameter: 25 (Shoulder diameter if included)

## Prompt
Create a professional shaft drawing (side view) with the following specifications:

- Shaft diameter: {shaft_diameter}mm
- Length: {shaft_length}mm
- Keyway: {keyway_width}mm wide × {keyway_depth}mm deep rectangular slot along length
- Shoulder: {include_shoulder} - if true, step to {shoulder_diameter}mm diameter at one end
- Chamfers: 1mm × 45° at both ends
- Representation: Side view as rectangle with keyway shown as rectangular cutout
- Layer organization: Outlines, CenterLines, Keyway
- Include center line through shaft axis
- Dimension annotations for critical features
- Tolerance callouts: h6 for shaft diameter (standard fit)

---

# Pulley - V-Belt
**Category**: mechanical
**Description**: V-belt pulley for power transmission

## Parameters
- pulley_diameter: 100 (Outer diameter in mm)
- groove_count: 2 (Number of V-belt grooves)
- bore_diameter: 20 (Center bore diameter in mm)
- hub_width: 40 (Hub width in mm)

## Prompt
Create a professional V-belt pulley drawing with the following specifications:

- Outer diameter: {pulley_diameter}mm
- Number of grooves: {groove_count}
- Groove profile: 40° V-shape (standard)
- Bore diameter: {bore_diameter}mm
- Hub width: {hub_width}mm (perpendicular to plane of view in side view)
- Rim thickness: 8mm
- Web thickness: 5mm (connecting hub to rim)
- Generate front view showing circular outline with grooves marked
- Layer organization: Outlines, CenterLines
- Include center lines (horizontal and vertical)
- Dimension annotations

---

# Sprocket - Chain Drive
**Category**: mechanical
**Description**: Chain drive sprocket

## Parameters
- num_teeth: 18 (Number of sprocket teeth)
- chain_pitch: 12.7 (Chain pitch in mm - standard 1/2" = 12.7mm)
- bore_diameter: 15 (Center bore diameter in mm)

## Prompt
Create a professional chain sprocket drawing with the following specifications:

- Number of teeth: {num_teeth}
- Chain pitch: {chain_pitch}mm
- Pitch diameter: ({num_teeth} × {chain_pitch}) / π (approximate)
- Bore diameter: {bore_diameter}mm
- Tooth profile: Simplified as small rectangular protrusions
- Tooth spacing: 360° / {num_teeth}
- Generate circles:
  - Pitch circle
  - Root circle (slightly smaller than pitch)
  - Bore circle
- Generate tooth profiles at proper spacing
- Layer organization: Outlines, CenterLines
- Include dimension annotations

---

# Flange Coupling
**Category**: mechanical
**Description**: Rigid flange coupling for shaft connection

## Parameters
- shaft_diameter: 25 (Shaft diameter to be coupled in mm)
- flange_diameter: 80 (Flange outer diameter in mm)
- bolt_circle_diameter: 60 (Bolt circle diameter in mm)
- num_bolts: 4 (Number of mounting bolts)
- bolt_size: 8 (Bolt hole diameter in mm)

## Prompt
Create a professional flange coupling drawing (front view) with the following specifications:

- Shaft bore: {shaft_diameter}mm diameter at center
- Flange outer diameter: {flange_diameter}mm
- Bolt circle diameter: {bolt_circle_diameter}mm
- Number of bolt holes: {num_bolts} evenly spaced around bolt circle
- Bolt hole diameter: {bolt_size}mm each
- Keyway in bore: {shaft_diameter}/4 mm wide (standard)
- Generate circles:
  - Flange outer circle
  - Bolt circle
  - Bolt holes at proper angular positions
  - Center bore
- Layer organization: Outlines, CenterLines, Holes
- Include center lines and dimension annotations
- Show hole pattern with angular spacing

---

# Washer - Flat
**Category**: mechanical
**Description**: Standard flat washer

## Parameters
- washer_size: M8 (Washer size matching bolt size)
- inner_diameter: 8.4 (Inner diameter in mm)
- outer_diameter: 16 (Outer diameter in mm)
- thickness: 1.6 (Washer thickness in mm)

## Prompt
Create a professional flat washer drawing with the following specifications:

- Washer designation: {washer_size}
- Inner diameter: {inner_diameter}mm
- Outer diameter: {outer_diameter}mm
- Thickness: {thickness}mm
- Generate two concentric circles (inner and outer)
- Layer organization: Outlines, CenterLines
- Include center lines (horizontal and vertical)
- Dimension annotations
- Front view (circular) showing both diameters
