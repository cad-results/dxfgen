# 1-Bedroom Apartment
**Category**: residential
**Description**: Compact 1-bedroom apartment with living area, kitchen, bathroom (approximately 50m²)

## Parameters
- total_area_m2: 50 (Total area in square meters)
- bedroom_width: 3000 (Bedroom width in mm)
- bedroom_length: 3500 (Bedroom length in mm)
- living_width: 4000 (Living room width in mm)
- living_length: 4000 (Living room length in mm)
- kitchen_width: 2500 (Kitchen width in mm)
- kitchen_length: 3000 (Kitchen length in mm)
- bathroom_width: 2000 (Bathroom width in mm)
- bathroom_length: 2000 (Bathroom length in mm)
- include_furniture: false (Include furniture layout)

## Prompt
Create a professional 1-bedroom apartment floor plan with the following specifications:

- Total area: approximately {total_area_m2}m²
- Bedroom: {bedroom_width}mm × {bedroom_length}mm with door and window
- Living room: {living_width}mm × {living_length}mm with windows on exterior wall
- Kitchen: {kitchen_width}mm × {kitchen_length}mm with counter space
- Bathroom: {bathroom_width}mm × {bathroom_length}mm with toilet, sink, shower
- Entrance hallway connecting all rooms
- All walls 200mm thick (exterior), 150mm thick (interior)
- Standard doors: 900mm wide, door swings
- Windows: 1200mm × 1200mm with frames
- Include furniture: {include_furniture}
- Organize on layers: Walls, Doors, Windows, Furniture (if included)

Layout: Entrance opens to hallway, bedroom on left, living room ahead, kitchen and bathroom on right.

---

# 3-Bedroom House
**Category**: residential
**Description**: Standard family home with 3 bedrooms, 2 bathrooms, living, kitchen, dining (approximately 150m²)

## Parameters
- total_area_m2: 150 (Total area in square meters)
- master_bedroom_size: 4000x3500 (Master bedroom dimensions in mm)
- bedroom2_size: 3000x3000 (Bedroom 2 dimensions in mm)
- bedroom3_size: 3000x3000 (Bedroom 3 dimensions in mm)
- living_room_size: 5000x4000 (Living room dimensions in mm)
- kitchen_size: 3000x3000 (Kitchen dimensions in mm)
- dining_size: 3000x3000 (Dining room dimensions in mm)
- bathroom_size: 2000x2000 (Bathroom dimensions in mm)
- master_ensuite: true (Include ensuite bathroom in master)
- include_furniture: false (Include furniture layout)

## Prompt
Create a professional 3-bedroom house floor plan with the following specifications:

- Total area: approximately {total_area_m2}m²
- Master bedroom: {master_bedroom_size}mm with ensuite: {master_ensuite}
- Bedroom 2: {bedroom2_size}mm
- Bedroom 3: {bedroom3_size}mm
- Living room: {living_room_size}mm
- Kitchen: {kitchen_size}mm with appliances marked
- Dining room: {dining_size}mm adjacent to kitchen
- Main bathroom: {bathroom_size}mm
- Master ensuite (if included): {bathroom_size}mm
- Entrance hallway and circulation paths
- All walls: 200mm thick (exterior), 150mm thick (interior)
- Doors: 900mm wide (interior), 1000mm (front door), all with swing arcs
- Windows: 1200mm × 1200mm standard, 1800mm × 1200mm large (living room)
- Include furniture: {include_furniture}
- Proper layer organization: Walls, Doors, Windows, Furniture, Fixtures

Layout: Entry to hallway, living room central with large windows, kitchen and dining open plan, bedrooms along one side with bathrooms.

---

# Office Layout
**Category**: commercial
**Description**: Open plan office with workstations, meeting rooms, reception (approximately 200m²)

## Parameters
- total_area_m2: 200 (Total office area in square meters)
- num_workstations: 12 (Number of workstation desks)
- num_meeting_rooms: 2 (Number of meeting rooms)
- include_reception: true (Include reception area)
- include_kitchen: true (Include break room/kitchen)
- include_restrooms: true (Include restroom facilities)
- workstation_type: open_plan (open_plan or cubicles)

## Prompt
Create a professional office layout with the following specifications:

- Total area: approximately {total_area_m2}m²
- Workstations: {num_workstations} desks in {workstation_type} arrangement
- Meeting rooms: {num_meeting_rooms} rooms (3m × 4m each) with table and chairs
- Reception area: {include_reception} - if true, include reception desk and waiting area
- Break room/kitchen: {include_kitchen} - if true, include 3m × 3m kitchen area
- Restrooms: {include_restrooms} - if true, include separate male/female restrooms (2m × 3m each)
- Storage/server room: 2m × 2m
- Walls: 150mm thick (interior partitions), 200mm thick (exterior)
- Doors: 900mm wide with glass markings for meeting rooms, 1000mm for entrance
- Windows: Multiple windows along exterior walls for natural light
- Ceiling height: 3000mm (commercial standard)
- Layer organization: Walls, Doors, Windows, Furniture, Fixtures

Layout: Reception at entrance, open workstations in center with natural light, meeting rooms along walls for privacy, kitchen and restrooms accessible from main area.

---

# Warehouse Layout
**Category**: industrial
**Description**: Industrial warehouse with loading dock, office, storage areas (approximately 500m²)

## Parameters
- total_area_m2: 500 (Total warehouse area in square meters)
- warehouse_width: 20000 (Main warehouse space width in mm)
- warehouse_length: 25000 (Main warehouse space length in mm)
- office_width: 5000 (Office area width in mm)
- office_length: 4000 (Office area length in mm)
- loading_docks: 2 (Number of loading dock bays)
- include_restroom: true (Include restroom facility)

## Prompt
Create a professional warehouse layout with the following specifications:

- Total area: approximately {total_area_m2}m²
- Main warehouse space: {warehouse_width}mm × {warehouse_length}mm open area
- Office area: {office_width}mm × {office_length}mm with desks, partition from warehouse
- Loading docks: {loading_docks} bays, 3000mm wide each, marked with door openings
- Storage racks: Rows of shelving units marked in warehouse area
- Restroom facility: {include_restroom} - if true, include 3m × 3m restroom
- Walls: 200mm thick concrete (exterior), 150mm for office partition
- Industrial doors: 3000mm wide for loading docks, 1000mm for personnel doors
- Office windows: 1200mm × 1200mm
- Warehouse height: 6000mm (indicated in annotations)
- Layer organization: Walls, Doors, Equipment, Office

Layout: Loading docks along one wall for truck access, office area in corner with window to warehouse, storage racks in organized rows with aisles, restroom accessible from office.

---

# Restaurant Floor Plan
**Category**: commercial
**Description**: Restaurant with dining area, kitchen, bar, restrooms (approximately 150m²)

## Parameters
- total_area_m2: 150 (Total restaurant area in square meters)
- dining_capacity: 40 (Seating capacity - number of seats)
- include_bar: true (Include bar area)
- kitchen_size: 6000x5000 (Kitchen dimensions in mm)
- dining_size: 10000x8000 (Dining area dimensions in mm)
- bar_length: 4000 (Bar counter length in mm if included)

## Prompt
Create a professional restaurant floor plan with the following specifications:

- Total area: approximately {total_area_m2}m²
- Dining area: {dining_size}mm with tables for approximately {dining_capacity} seats
- Kitchen: {kitchen_size}mm with prep areas, cooking line, dishwashing marked
- Bar area: {include_bar} - if true, include bar counter {bar_length}mm long with back bar
- Host stand: At entrance for seating management
- Restrooms: Separate male/female facilities (2m × 3m each)
- Storage: Dry storage and walk-in cooler areas marked
- Walls: 200mm thick (exterior), 150mm (interior)
- Doors: 1200mm wide (entrance for accessibility), 900mm interior, 1500mm kitchen service doors
- Windows: Large windows along dining area exterior for ambiance
- Emergency exits: Marked on opposite sides
- Layer organization: Walls, Doors, Windows, Furniture, Kitchen Equipment, Fixtures

Layout: Entrance with host stand, dining area with tables (2-person, 4-person mix), bar along one side, kitchen at rear with service window to dining, restrooms accessible from dining area.

---

# Studio Apartment
**Category**: residential
**Description**: Efficient studio apartment with combined living/sleeping, kitchenette, bathroom (approximately 35m²)

## Parameters
- total_area_m2: 35 (Total area in square meters)
- main_room_width: 5000 (Combined living/sleeping area width in mm)
- main_room_length: 6000 (Combined living/sleeping area length in mm)
- kitchenette_length: 2500 (Kitchenette length along wall in mm)
- bathroom_size: 2000x2000 (Bathroom dimensions in mm)
- include_furniture: true (Include furniture to show space division)

## Prompt
Create a professional studio apartment floor plan with the following specifications:

- Total area: approximately {total_area_m2}m²
- Main room: {main_room_width}mm × {main_room_length}mm (combined living/sleeping area)
- Kitchenette: {kitchenette_length}mm along one wall with counter, sink, compact appliances
- Bathroom: {bathroom_size}mm with toilet, sink, shower
- Entrance alcove with closet space
- All walls: 200mm thick (exterior), 150mm (interior/bathroom)
- Door: 900mm wide entrance, 800mm bathroom
- Windows: 1200mm × 1200mm, multiple for natural light
- Include furniture: {include_furniture} (bed area, sofa/seating, dining table to show zoning)
- Layer organization: Walls, Doors, Windows, Furniture, Fixtures

Layout: Entrance opens to main space, kitchenette immediately accessible, bathroom off entrance, main room with furniture zoning sleeping area from living area, windows for maximum light.
