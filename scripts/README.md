# DXF Generator Scripts

Interactive viewers and utilities for DXF CAD files, optimized for WSL2 environments.

---

## Quick Start

### Start the Server

```bash
cd /home/adminho/dxfgen

# Option 1: Direct Python
python -m backend.server

# Option 2: Using start script (sets up conda env)
./start.sh
```

Open browser at: http://localhost:5001

### Generate DXF via Command Line

```bash
# Interactive test menu
python test_workflow.py

# Direct generation with prompt
python test_workflow.py "Draw a square 100mm on each side"

# API client example
python api_example.py
```

---

## DXF Viewer (2D CAD Drawings)

View DXF files with interactive pan/zoom capabilities.

### Usage

```bash
cd /home/adminho/dxfgen/scripts

# View a single DXF file
./run_dxf_viewer.sh ../output/square.dxf

# Browse all DXF files in a directory
./run_dxf_viewer.sh --browse ../output/

# View sample files
./run_dxf_viewer.sh ../backend/text_to_dxf/samples/circle.dxf
./run_dxf_viewer.sh ../backend/text_to_dxf/samples/butterfly.dxf
```

### Sample Commands

Generate and view sample DXF drawings:

```bash
cd /home/adminho/dxfgen

# 1. Square (100mm sides)
python test_workflow.py "Draw a square 100mm on each side"

# 2. Concentric circles (radii 20, 40, 60mm)
python test_workflow.py "Three concentric circles with radii 20mm, 40mm, and 60mm"

# 3. Rectangle with centered circle
python test_workflow.py "Draw a rectangle 150mm x 80mm with a circle of radius 30mm in the center"

# View the generated files
cd scripts
./run_dxf_viewer.sh ../output/square.dxf
./run_dxf_viewer.sh ../output/concentric_circles.dxf
./run_dxf_viewer.sh ../output/rect_with_circle.dxf
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| S | Save screenshot |
| G | Toggle grid |
| I | Show file info |
| R | Reset view |
| A / LEFT | Previous file (browse mode) |
| D / RIGHT | Next file (browse mode) |
| H | Show help |
| Q / ESC | Quit viewer |

### Mouse Controls (Matplotlib Toolbar)

- **Pan tool**: Click and drag to pan
- **Zoom tool**: Click and drag to zoom rectangle
- **Scroll wheel**: Zoom in/out
- **Home button**: Reset view to fit all

---

## 3D Mesh Viewer (PartField)

View GLB, PLY, OBJ, STL files with part segmentation overlays.

### Usage

```bash
cd /home/adminho/dxfgen/scripts

# View a 3D mesh file
./run_viewer.sh model.glb

# Browse all mesh files in a directory
./run_viewer.sh --browse ../data/meshes/
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| T / TAB | Cycle views: Original → Segmented → BBoxes → PCA |
| C | Next clustering result |
| V | Previous clustering result |
| A / LEFT | Previous file (browse mode) |
| D / RIGHT | Next file (browse mode) |
| S | Save screenshot |
| R | Reset camera view |
| H | Toggle help |
| Q / ESC | Exit viewer |

---

## API Usage

### Start Server

```bash
python -m backend.server
# Server runs at http://localhost:5000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Process natural language input |
| `/api/generate` | POST | Generate DXF from session |
| `/api/download/<filename>` | GET | Download generated file |
| `/api/formats` | GET | Get available export formats |
| `/api/convert` | POST | Convert file to another format |
| `/api/generate-and-convert` | POST | Generate and convert in one step |
| `/api/view` | POST | Launch 3D viewer for a file |
| `/api/viewer/status` | GET | Check 3D viewer availability |
| `/api/health` | GET | Server health check |

### Example API Call

```bash
# Generate a drawing via API
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "draw a 50mm circle", "session_id": "test123"}'
```

---

## Example Prompts

### Beginner
- "Draw a circle radius 50mm"
- "Create a rectangle 100mm x 60mm"
- "Draw a square 75mm on each side"

### Intermediate
- "Three concentric circles with radii 20, 40, 60mm"
- "Rectangle 120mm x 80mm with 10mm radius circles at each corner"
- "Equilateral triangle with 80mm sides"

### Advanced
- "Floor plan of a 5m x 4m room with a 900mm door opening"
- "Gear with 8 teeth around a 60mm circle"
- "Mechanical flange: 100mm diameter with four 10mm mounting holes"

### Templates
- "use 3-bedroom house template"
- "use 1-bedroom apartment template"
- "use small office template"

---

## File Locations

| Item | Path |
|------|------|
| Generated DXF files | `/home/adminho/dxfgen/output/` |
| Sample DXF files | `/home/adminho/dxfgen/backend/text_to_dxf/samples/` |
| Server | `/home/adminho/dxfgen/backend/server.py` |
| Test scripts | `/home/adminho/dxfgen/test_workflow.py`, `api_example.py` |

---

## WSL2 Requirements

Both viewers are configured for WSL2 with WSLg or X11 forwarding.

### WSLg (Windows 11)
Works automatically - no additional setup needed.

### X11 Server (Windows 10)
Install VcXsrv or X410 on Windows, then:
```bash
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
```

### Dependencies

```bash
# For DXF viewer
pip install ezdxf[draw] matplotlib

# For 3D mesh viewer
pip install open3d trimesh matplotlib Pillow
```

---

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
# Create .env file with your API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### "Port 5000 already in use"
```bash
# Change port in .env
echo "FLASK_PORT=5001" >> .env
```

### "text_to_dxf not found"
```bash
git clone https://github.com/GreatDevelopers/text_to_dxf.git backend/text_to_dxf
```

---

For detailed documentation, see:
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [README.md](../README.md) - Full documentation
