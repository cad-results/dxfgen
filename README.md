# DXF Generator Chatbot - Professional CAD from Natural Language

Transform natural language descriptions into professional-grade DXF CAD files instantly. No CAD experience required!

## 🚀 Quick Start

```bash
# 1. Set your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# 2. Start the server
python -m backend.server

# 3. Open your browser
# Navigate to http://localhost:5000

# 4. Configure settings (click ⚙️ Settings button)
# - Check or uncheck "Auto-accept validation fixes"
# - Save settings

# 5. Start creating!
```

---

## 🎛️ Auto-Accept Mode: ON vs OFF

### What is Auto-Accept Mode?

**Auto-Accept Mode** determines how the system handles vague inputs and validation:

- **✅ ON (Streamlined)**: System automatically refines vague queries and fixes issues without asking
- **⬜ OFF (Careful)**: System shows each refinement step and asks for user confirmation

---

## 📝 Example Prompts - Auto-Accept ✅ ON

> **Best for**: Fast workflow, trust AI defaults, production use

### Floor Plans

#### Prompt 1: Vague Input (System Refines Automatically)
```
Input: "build a house"

What Happens:
1. ✅ System detects vague input
2. ✅ Automatically refines to: "3-bedroom house, 150m², master 4m×3.5m, bedrooms 3m×3m..."
3. ✅ Routes to Floor Plan Specialist
4. ✅ Generates complete floor plan with:
   - Walls (200mm exterior, 150mm interior)
   - Doors (900mm with swing arcs)
   - Windows (1200mm × 1200mm)
   - All rooms properly connected
5. ✅ Auto-fixes: Removes duplicate points, assigns layers
6. ✅ Output: Professional DXF file

User Questions: 0 (Zero!)
Time: ~30 seconds
```

#### Prompt 2: Medium Detail
```
Input: "Create a 2-bedroom apartment with kitchen and bathroom"

What Happens:
1. ✅ Refines to specific dimensions automatically
2. ✅ Generates 50m² apartment layout
3. ✅ Bedrooms: 3m × 3.5m each
4. ✅ Kitchen: 2.5m × 3m
5. ✅ Bathroom: 2m × 2m
6. ✅ Living area: 4m × 4m
7. ✅ Auto-validates and fixes

User Questions: 0
Time: ~25 seconds
```

#### Prompt 3: Detailed Input (No Refinement Needed)
```
Input: "3-bedroom house with master bedroom 4m×3.5m, two bedrooms 3m×3m each,
       2 bathrooms 2m×2m, living room 5m×4m, kitchen 3m×3m, dining 3m×3m"

What Happens:
1. ✅ System recognizes complete specification
2. ✅ Skips refinement (not needed)
3. ✅ Directly generates floor plan
4. ✅ All dimensions exactly as specified
5. ✅ Professional output

User Questions: 0
Time: ~20 seconds
```

#### Prompt 4: Commercial Space
```
Input: "design an office for 10 people"

What Happens:
1. ✅ Refines to: "100m² office, 10 workstations, 1 meeting room, reception, break room"
2. ✅ Generates open plan layout
3. ✅ Includes: workstations, meeting room (3m×4m), kitchen, restrooms
4. ✅ Commercial standards: 3m ceiling height, accessibility compliant

User Questions: 0
Time: ~30 seconds
```

#### Prompt 5: Industrial
```
Input: "small warehouse with loading dock"

What Happens:
1. ✅ Refines to: "300m² warehouse, 15m×20m space, office 4m×4m, 2 loading docks"
2. ✅ Generates industrial layout
3. ✅ Loading docks: 3m wide each
4. ✅ Storage racks marked
5. ✅ Office area partitioned

User Questions: 0
Time: ~30 seconds
```

### Mechanical Parts

#### Prompt 6: Simple Gear
```
Input: "create a gear"

What Happens:
1. ✅ Refines to: "20-tooth spur gear, module 2.5, bore 10mm"
2. ✅ Routes to Mechanical Specialist
3. ✅ Calculates: Pitch ⌀ 50mm, Outer ⌀ 55mm, Root ⌀ 43.75mm
4. ✅ Generates all circles + 20 tooth profiles
5. ✅ Includes center lines

User Questions: 0
Time: ~20 seconds
```

#### Prompt 7: Detailed Gear
```
Input: "40-tooth gear, module 3mm, bore 25mm with keyway"

What Happens:
1. ✅ No refinement needed (fully specified)
2. ✅ Generates: PD=120mm, OD=126mm, RD=112.5mm
3. ✅ 40 evenly spaced teeth
4. ✅ Keyway: 8mm wide rectangular slot
5. ✅ Professional engineering drawing

User Questions: 0
Time: ~25 seconds
```

#### Prompt 8: Bearing
```
Input: "ball bearing 6205"

What Happens:
1. ✅ Recognizes standard bearing designation
2. ✅ Applies specs: Bore 25mm, OD 52mm, Width 15mm
3. ✅ Generates concentric circles (outer race, ball pitch, inner race)
4. ✅ Section view representation

User Questions: 0
Time: ~15 seconds
```

#### Prompt 9: Fastener
```
Input: "M8 bolt 40mm long"

What Happens:
1. ✅ Applies ISO standards: Hex head 13mm, thread 8mm
2. ✅ Generates hexagonal head (6-point polyline)
3. ✅ Shaft 40mm length
4. ✅ Thread representation included

User Questions: 0
Time: ~15 seconds
```

### Using Templates

#### Prompt 10: Template Selection
```
Input: "use 3-bedroom house template"

What Happens:
1. ✅ Loads pre-defined template with all specifications
2. ✅ No refinement needed (template is complete)
3. ✅ Generates professional house instantly
4. ✅ All rooms, doors, windows included

User Questions: 0
Time: ~15 seconds (fastest option!)
```

### Augmentation

#### Prompt 11: Modify Existing Design
```
After generating a floor plan:

Input: "add a window to the north wall of the master bedroom"

What Happens:
1. ✅ Augmentation Agent analyzes current design
2. ✅ Identifies north wall automatically
3. ✅ Calculates optimal window position (centered)
4. ✅ Adds 1200mm window opening + frames
5. ✅ Assigns to Windows layer
6. ✅ Regenerates metadata

User Questions: 0
Time: ~20 seconds
```

---

## 📝 Example Prompts - Auto-Accept ⬜ OFF

> **Best for**: Learning, precision control, reviewing AI decisions

### Floor Plans

#### Prompt 1: Vague Input (System Shows Refinement)
```
Input: "build a house"

What Happens:
1. 💬 System: "I understand you want to create a residential house,
              but specific room count, layout, and dimensions not specified."
2. 💬 System: "Missing: number of bedrooms, bathrooms, total area, room dimensions"
3. 💬 System: "Suggested defaults: 3 bedrooms, 2 bathrooms, 150m², single-story"
4. ❓ User prompted: "Should I apply these defaults?"
5. 👤 User: "Yes" or modify specifications
6. 💬 System shows refined spec: "3-bedroom house with master 4m×3.5m..."
7. ❓ User: "Generate with these specifications?"
8. 👤 User: "Yes"
9. ✅ Generates floor plan
10. 💬 System: "Found 3 duplicate points. Should I remove them?"
11. 👤 User: "Yes"
12. ⚠️ System: "Some entities on layer 0. Assign to proper layers?"
13. 👤 User: "Yes"
14. ✅ Output: Professional DXF file

User Questions: 4-6
Time: ~2-3 minutes (depends on user response time)
Benefits: Full control, learn what system is doing
```

#### Prompt 2: Medium Detail
```
Input: "Create a 2-bedroom apartment with kitchen and bathroom"

What Happens:
1. 💬 System: "2-bedroom apartment, but specific dimensions not provided"
2. 💬 Suggested: "Bedroom 1: 3m×3.5m, Bedroom 2: 3m×3m, Kitchen: 2.5m×3m..."
3. ❓ User: Review and approve or modify
4. ✅ Generates
5. 💬 Validation results shown with issues
6. ❓ User: Confirm fixes
7. ✅ Final output

User Questions: 2-3
Time: ~1-2 minutes
```

#### Prompt 3: Detailed Input
```
Input: "3-bedroom house with master bedroom 4m×3.5m, two bedrooms 3m×3m each,
       2 bathrooms 2m×2m, living room 5m×4m, kitchen 3m×3m"

What Happens:
1. 💬 System: "Complete specification received, no refinement needed"
2. 💬 Main entities: polylines (rooms), lines (walls), arcs (door swings)
3. ✅ Generates floor plan
4. 💬 Validation: "All checks passed, confidence 95%"
5. 💬 Minor suggestions shown (if any)
6. ❓ User: "Generate DXF?"
7. 👤 User: "Yes"
8. ✅ Output

User Questions: 1-2
Time: ~1 minute
```

### Mechanical Parts

#### Prompt 4: Simple Gear
```
Input: "create a gear"

What Happens:
1. 💬 System: "Gear specifications incomplete"
2. 💬 Missing: "number of teeth, module/pitch, diameter, bore size"
3. 💬 Suggested defaults: "20 teeth, module 2.5mm, bore 10mm"
4. ❓ User: Approve or specify different values
5. 👤 User: "Use defaults" or "Make it 30 teeth, module 3"
6. 💬 System calculates and shows: "PD=50mm, OD=55mm, RD=43.75mm"
7. ❓ User: "Correct?"
8. 👤 User: "Yes"
9. ✅ Generates gear

User Questions: 2-3
Time: ~1-2 minutes
```

### Augmentation

#### Prompt 5: Modify Design
```
After generating a floor plan:

Input: "add a window to the north wall of the master bedroom"

What Happens:
1. 💬 System: "Identified north wall at coordinates..."
2. 💬 "Window position calculated: centered at X=2400mm"
3. 💬 "Window size: 1200mm (standard). Change?"
4. ❓ User: Approve position and size
5. 👤 User: "Yes" or "Make it 1800mm wide"
6. ✅ Adds window
7. 💬 Changes made: "Added window opening, frame marks, assigned to Windows layer"
8. ✅ Updated DXF

User Questions: 1-2
Time: ~1 minute
```

---

## 🎯 Which Mode Should You Use?

### Use Auto-Accept ✅ ON When:
- ✅ You trust AI defaults
- ✅ You want fast results
- ✅ You're prototyping / iterating quickly
- ✅ Input is relatively vague ("build a house")
- ✅ You're comfortable with industry standards
- ✅ Production workflow

### Use Auto-Accept ⬜ OFF When:
- ✅ You're learning the system
- ✅ You need precise control
- ✅ You want to see refinement steps
- ✅ Critical/custom specifications
- ✅ Educational purposes
- ✅ Quality assurance review

---

## 💡 Tips for Best Prompts

### For Floor Plans

**Good Vague Prompts** (Auto-Accept ON):
- "build a small apartment"
- "design a house"
- "create an office space"
- "warehouse with loading dock"

**Good Detailed Prompts** (Any Mode):
- "3-bedroom house with master 4m×3.5m ensuite, bedrooms 3m×3m, living 5m×4m, kitchen 3m×3m, 2 bathrooms"
- "Studio apartment 35m² with kitchenette along one wall, bathroom 2m×2m, main room 5m×6m"
- "Office 100m² with 8 workstations, meeting room 3m×4m, reception, break room, restrooms"

**Template Prompts** (Fastest):
- "use 1-bedroom apartment template"
- "3-bedroom house template"
- "small office template"

### For Mechanical Parts

**Good Vague Prompts** (Auto-Accept ON):
- "create a gear"
- "design a bearing"
- "M8 bolt"

**Good Detailed Prompts** (Any Mode):
- "40-tooth spur gear, module 3mm, bore 25mm with 8mm keyway"
- "Ball bearing 6205 (bore 25mm, OD 52mm, width 15mm)"
- "M10 hex bolt, 60mm length, with thread representation"

### For Augmentation

**Good Prompts**:
- "add a window to the north wall"
- "make the door wider"
- "move the bed to the opposite wall"
- "add a table in the center"
- "remove the small chair"

---

## 📋 Complete Example Session

### Session 1: Quick Floor Plan (Auto-Accept ON)

```
👤 User: [Opens browser, clicks ⚙️ Settings]
👤 User: [Checks "Auto-accept validation fixes"]
👤 User: [Clicks "Save Settings"]

👤 User: "create a 2-bedroom apartment"

🤖 System: "Specification refined automatically (confidence: 85%)"
🤖 System: "Extracted 147 geometric entities using floorplan specialist:
           - Lines: 96 (walls)
           - Arcs: 12 (door swings)
           - Polylines: 8 (room outlines)"

🤖 System: "✓ Validation passed (confidence: 92%)

           Auto-fixes applied (3):
           - Removed 2 duplicate points from polyline 'Kitchen Wall'
           - Assigned layer 'Doors' to arc 'Front Door Swing'
           - Normalized angle from 365° to 5° for arc 'Bathroom Door'"

🤖 System: "Metadata has been formatted. Ready to generate DXF!"

👤 User: [Clicks "Generate DXF File"]
🤖 System: "DXF file 'apartment_2br.dxf' generated successfully!"
👤 User: [Clicks "Download DXF File"]

✅ Done! Total time: ~45 seconds
```

### Session 2: Custom Gear (Auto-Accept OFF)

```
👤 User: [Opens browser, keeps auto-accept OFF]

👤 User: "create a gear for a bike"

🤖 System: "I understand you want to create a mechanical gear,
           but specifications are incomplete.

           Missing: number of teeth, module/pitch, diameter, bore size

           For a bike gear (typical), I suggest:
           - Number of teeth: 32 (common for bike chainring)
           - Module: 4mm (bike chain pitch compatible)
           - Bore: 20mm (for standard crank mounting)

           Should I use these defaults, or would you like to specify?"

👤 User: "use defaults"

🤖 System: "Refined specification:
           - 32-tooth sprocket gear
           - Module: 4mm
           - Pitch diameter: 128mm
           - Outer diameter: 136mm
           - Root diameter: 118mm
           - Bore: 20mm
           - Chain compatible: Yes (ISO bike chain)

           Generate with these specifications?"

👤 User: "yes"

🤖 System: "Extracted 70 geometric entities using mechanical specialist:
           - Circles: 4 (outer, pitch, root, bore)
           - Lines: 64 (32 tooth profiles, each 2 lines)
           - Center lines included"

🤖 System: "Validation results:
           ✓ All geometries valid
           ✓ No duplicate points
           ✓ Layers properly assigned
           Confidence: 98%

           Minor suggestion: Consider adding keyway for crank mounting

           Proceed with generation?"

👤 User: "yes"

👤 User: [Clicks "Generate DXF File"]
🤖 System: "DXF file 'bike_gear_32t.dxf' generated successfully!"

✅ Done! Total time: ~3 minutes (including user decisions)
```

---

## 🚀 More Example Prompts

### Residential
- "studio apartment"
- "1-bedroom apartment with open kitchen"
- "3-bedroom house with garage"
- "2-story house with 4 bedrooms"
- "townhouse with 3 floors"

### Commercial
- "small office for 6 people"
- "retail shop 80m²"
- "restaurant with 40 seats"
- "hotel reception area"
- "gym 200m²"

### Industrial
- "warehouse 500m²"
- "factory floor with assembly line"
- "storage facility"
- "workshop with tool storage"

### Mechanical
- "12-tooth gear"
- "bearing for 20mm shaft"
- "M10 bolt 50mm"
- "shaft with keyway"
- "pulley 100mm diameter"

---

## 📚 System Capabilities

### What You Can Create:

**Residential**: Houses, apartments, studios, condos, townhouses
**Commercial**: Offices, retail, restaurants, hotels, gyms
**Industrial**: Warehouses, factories, workshops, storage
**Mechanical**: Gears, bearings, fasteners, shafts, pulleys, sprockets
**Elements**: Doors, windows, stairs, furniture, kitchen, bathrooms

---

## 🎓 Learning Path

**Beginner** (Start here):
1. Enable auto-accept mode
2. Try simple prompts: "build a house"
3. See what system generates
4. Use augmentation to refine

**Intermediate**:
1. Try both modes (ON and OFF)
2. Use detailed prompts
3. Explore templates
4. Learn standard dimensions

**Advanced**:
1. Complex multi-room layouts
2. Custom dimensions throughout
3. Mechanical assemblies
4. Template customization

---

**Ready to create professional CAD drawings? Start with a simple prompt and watch the magic happen!** 🎨✨

---

For complete documentation, see:
- `COMPLETE_IMPLEMENTATION_GUIDE.md` - Detailed usage guide
- `IMPLEMENTATION_SUMMARY.md` - Technical overview

**Version**: 1.0.0 | **Status**: Production Ready

---

## 🔄 Multi-Format Export & 3D Visualization (Mayo Integration)

DXF Generator now includes powerful file conversion and 3D visualization capabilities powered by Mayo.

### Supported Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **DXF** | AutoCAD Drawing Exchange | Default, universal CAD compatibility |
| **STEP** | Standard for Exchange of Product Data | CAD/CAM interchange, manufacturing |
| **IGES** | Initial Graphics Exchange Specification | Legacy CAD systems |
| **STL** | Stereolithography | 3D printing, rapid prototyping |
| **OBJ** | Wavefront Object | 3D modeling, game engines |
| **PLY** | Polygon File Format | Point clouds, 3D scanning |
| **GLTF** | GL Transmission Format | Web 3D, AR/VR applications |
| **OFF** | Object File Format | Mesh processing |

### How to Use Multi-Format Export

1. **Generate your design** using any prompt (floor plan, mechanical part, etc.)
2. **Select output format** from the dropdown menu in the metadata panel
3. **Click "Generate File"** - the system will:
   - First create the DXF file
   - Then convert to your selected format using Mayo
4. **Download** your file in the chosen format

```
Example Workflow:

👤 User: "create a 2-bedroom apartment"
🤖 System: [Generates metadata]

👤 User: [Selects "STL (3D Printing)" from dropdown]
👤 User: [Clicks "Generate File"]

🤖 System: "STL file 'apartment_2br.stl' generated successfully!"
         [Download File] [Download DXF] buttons appear
```

### 3D Visualization

For viewable formats (OBJ, PLY, STL, GLTF, GLB, OFF), a **"View in 3D"** button appears after generation.

**Viewer Features:**
- Interactive 3D rotation and zoom
- Multiple view modes (Original, Segmented, Bounding Boxes, PCA Features)
- Keyboard controls:
  - `T/TAB` - Cycle view modes
  - `R` - Reset camera
  - `S` - Save screenshot
  - `H` - Show help
  - `ESC/Q` - Exit

```
Example:

👤 User: "create a gear"
👤 User: [Selects "OBJ (3D Model)"]
👤 User: [Clicks "Generate File"]

🤖 System: "OBJ file 'gear_20t.obj' generated!"
👤 User: [Clicks "View in 3D"]

🤖 System: "3D viewer launched. Check your display for the viewer window."
         [Interactive 3D viewer opens with the gear model]
```

### API Endpoints for Conversion

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/formats` | GET | Get available export formats |
| `/api/generate-and-convert` | POST | Generate DXF and convert to selected format |
| `/api/convert` | POST | Convert an existing file to a new format |
| `/api/view` | POST | Launch 3D viewer for a file |
| `/api/viewer/status` | GET | Check if 3D viewer is available |

**Example API Usage:**

```python
import requests

# Generate and convert to STEP format
response = requests.post('http://localhost:5000/api/generate-and-convert', json={
    'session_id': 'my_session',
    'csv_metadata': '...your metadata...',
    'format': 'STEP'
})

result = response.json()
# {
#   'success': True,
#   'filename': 'drawing_12345.step',
#   'format': 'STEP',
#   'download_url': '/api/download/drawing_12345.step',
#   'dxf_filename': 'drawing_12345.dxf',
#   'dxf_download_url': '/api/download/drawing_12345.dxf'
# }
```

### Requirements for 3D Viewer

The 3D viewer requires additional dependencies (automatically installed):
- `open3d` - 3D visualization
- `trimesh` - Mesh processing
- `matplotlib` - Color mapping
- `Pillow` - Image processing

**WSL2 Users:** The viewer includes automatic display configuration for WSL2 environments. Ensure you have WSLg enabled or an X server (VcXsrv, X410) running.

### Format Selection Tips

| If you need... | Choose |
|----------------|--------|
| Universal CAD compatibility | DXF |
| Manufacturing/CNC | STEP |
| 3D printing | STL |
| Web visualization | GLTF |
| Point cloud analysis | PLY |
| 3D modeling software | OBJ |

---
