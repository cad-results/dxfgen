# Curve and BRep Support for DXF Generator

This document describes the nonlinear curve and BRep (Boundary Representation) support added to the DXF Generator chatbot.

## Overview

The system now supports both linear (polygon-based) and nonlinear curve geometries:

### Basic Entities (Original)
- **Lines (L)**: Straight line segments
- **Circles (C)**: Full circles
- **Arcs (A)**: Circular arcs
- **Polylines (P)**: Connected line segments
- **Hatches (H)**: Filled regions

### Curve Entities (New)
- **B-Splines (S)**: Non-rational B-spline curves
- **NURBS (N)**: Non-Uniform Rational B-Splines
- **Bezier (B)**: Bezier curves of any degree
- **Ellipses (E)**: Ellipses and elliptical arcs
- **Curved Polylines (PW)**: Polylines with arc segments (bulge)

## Mathematical Foundation

### Bezier Curves

**Definition**:
```
B(t) = Σ C(n,i) · (1-t)^(n-i) · t^i · P_i  for i = 0 to n
```

Where:
- `n` is the degree (number of control points - 1)
- `C(n,i)` is the binomial coefficient
- `P_i` are control points
- `t ∈ [0, 1]` is the parameter

**Properties**:
- Passes through first and last control points
- Tangent at endpoints aligns with control polygon edges
- Contained within convex hull of control points
- Implemented using de Casteljau's algorithm for numerical stability

### B-Spline Curves

**Definition**:
```
C(u) = Σ N_{i,p}(u) · P_i  for i = 0 to n
```

Where:
- `N_{i,p}(u)` are B-spline basis functions (Cox-de Boor recursion)
- `p` is the degree
- `P_i` are control points

**Basis Function Recursion**:
```
N_{i,0}(u) = 1 if u_i ≤ u < u_{i+1}, else 0

N_{i,p}(u) = (u - u_i)/(u_{i+p} - u_i) · N_{i,p-1}(u)
           + (u_{i+p+1} - u)/(u_{i+p+1} - u_{i+1}) · N_{i+1,p-1}(u)
```

**Knot Vector Types**:
- **Uniform**: Evenly spaced knots
- **Clamped (Open)**: Curve passes through endpoints (default)
- **Non-uniform**: Arbitrary knot spacing

### NURBS Curves

**Definition**:
```
C(u) = Σ R_{i,p}(u) · P_i

R_{i,p}(u) = (N_{i,p}(u) · w_i) / Σ(N_{j,p}(u) · w_j)
```

Where `w_i` are weights.

**Weight Effects**:
- `w > 1`: Curve pulled toward control point
- `w < 1`: Curve pushed away from control point
- `w = 1`: Standard B-spline behavior

**Conic Sections**:
NURBS can exactly represent circles, ellipses, parabolas, and hyperbolas:
- Circle arc middle weight: `w = cos(half_angle)`

### Polyline Bulge

**Bulge Formula**:
```
bulge = tan(included_angle / 4)
```

- `bulge = 0`: Straight segment
- `bulge > 0`: Arc curves counter-clockwise (left)
- `bulge < 0`: Arc curves clockwise (right)
- `|bulge| = 1`: Semicircle (180°)
- `|bulge| ≈ 0.414`: Quarter circle (90°)

**Arc Geometry from Bulge**:
```
sagitta = |bulge| · chord_length / 2
radius = (chord_length² / 4 + sagitta²) / (2 · sagitta)
```

## BRep (Boundary Representation)

### Data Structures

```
BRepVertex: Point in 3D space
    ↓
BRepEdge: Curve bounded by two vertices
    ↓
BRepLoop: Closed sequence of edges (face boundary)
    ↓
BRepFace: Surface region bounded by loops
    ↓
BRepShell: Collection of connected faces
    ↓
BRepSolid: 3D region bounded by closed shells
```

### Edge Types

| Type | Parameters | Use Case |
|------|------------|----------|
| LINE | start, end | Straight edges |
| ARC | center, radius, angles | Circular edges |
| BEZIER | control points | Smooth curves |
| BSPLINE | control points, degree, knots | Complex curves |
| NURBS | control points, weights, degree, knots | Exact conics |

### Edge Parameter Calculations

**Arc from Bulge**:
```python
params = calculate_edge_parameters(
    EdgeType.ARC,
    start_point, end_point,
    bulge=0.5  # Arc bulge value
)
# Returns: center, radius, start_angle, end_angle
```

**Arc from Three Points**:
```python
params = calculate_edge_parameters(
    EdgeType.ARC,
    start_point, end_point,
    midpoint=mid_point  # Point on arc
)
# Calculates circumcircle through three points
```

**Bezier from Tangents**:
```python
params = calculate_edge_parameters(
    EdgeType.BEZIER,
    start_point, end_point,
    tangent_start={'x': 1, 'y': 1},
    tangent_end={'x': 1, 'y': -1}
)
# Creates cubic Bezier with specified tangent directions
```

## Usage Examples

### Natural Language Triggers

The chatbot recognizes curve requirements from descriptions like:

- "Create a **smooth curve** through these points..."
- "Draw a **Bezier** profile for..."
- "Generate a **B-spline** contour..."
- "Create a **NURBS** representation of a circle..."
- "Design an **organic/flowing** shape..."
- "Make an **airfoil** profile..."
- "Draw an **ellipse** with..."

### API Usage

```python
from backend.dxf_generator import DXFGenerator

entities = {
    'splines': [{
        'control_points': [
            {'x': 0, 'y': 0},
            {'x': 50, 'y': 100},
            {'x': 100, 'y': 0}
        ],
        'degree': 3,
        'layer': 'Curves'
    }],
    'bezier_curves': [{
        'control_points': [
            {'x': 0, 'y': 200},
            {'x': 30, 'y': 250},
            {'x': 70, 'y': 250},
            {'x': 100, 'y': 200}
        ],
        'layer': 'Bezier'
    }],
    'ellipses': [{
        'center_x': 150,
        'center_y': 100,
        'major_axis_x': 50,
        'major_axis_y': 0,
        'ratio': 0.6,
        'layer': 'Ellipses'
    }]
}

generator = DXFGenerator()
success, path, error = generator.generate_with_curves(entities, 'output.dxf')
```

## Architecture

### Module Structure

```
backend/
├── math_core/              # Mathematical foundations
│   ├── __init__.py
│   ├── geometry.py         # Points, vectors, polygons
│   ├── curves.py           # Bezier, B-Spline, NURBS, interpolation
│   └── brep.py             # BRep data structures and calculations
│
├── agents/
│   ├── curve_entities.py   # Pydantic models for curve types
│   ├── curve_specialist.py # Curve-focused entity extraction
│   └── ... (other agents)
│
├── text_to_dxf/
│   └── curve_processing.py # DXF curve entity creation
│
└── dxf_generator.py        # Extended with generate_with_curves()
```

### Workflow Integration

```
User Input (e.g., "PART ID OP22-0002L ARM ASSEMBLY, SS 25"-29" D.O.")
    ↓
Intent Parser
├── Detects part numbers (OP22-0002L, 160CP19, 168255, etc.)
├── Identifies manufacturer (GAL, Global Industrial, PartsTown)
├── Sets requires_research=True
├── Sets requires_curves based on design type
└── Generates research_query
    ↓
Research Agent (if requires_research=True)
├── Step 1: Check built-in specifications database
├── Step 2: Google/web search for specifications
├── Step 3: Search for and download PDF catalogs
├── Step 4: Extract text from PDFs (PyMuPDF, pypdf, pdfplumber)
├── Step 5: Analyze technical images/drawings (vision model)
├── Step 6: Cross-reference multiple sources
└── Step 7: LLM synthesis of all gathered data
    ↓
[Route based on complexity]
├── Simple: General Entity Extractor
├── Floorplan: Floor Plan Specialist
├── Mechanical: Mechanical Specialist
├── Curves: Curve Specialist
└── Complex/Industrial: Advanced Curve Specialist
    ↓
Extended Entities (includes splines, NURBS, Bezier, ellipses)
    ↓
Metadata Formatter (extended CSV format)
    ↓
DXF Generator (generate_with_curves method)
    ↓
DXF File with native curve entities
```

## Research Capabilities

The Research Agent provides extensive web research for accurate product specifications:

### Search Methods
- **Google Custom Search API** (if API key provided)
- **SerpAPI** (fallback)
- **DuckDuckGo Instant Answers** (no API key required)

### PDF Extraction
Supports multiple PDF libraries:
- **PyMuPDF (fitz)**: Fast, handles most PDFs
- **pypdf**: Pure Python fallback
- **pdfplumber**: Best for tables and structured data

### Image Analysis
Uses vision-capable LLM to analyze:
- Technical drawings with dimensions
- Catalog product images
- Engineering diagrams
- Blueprint excerpts

### Built-in Specifications Database
Pre-loaded with common industrial parts:

| Source | Part Numbers | Examples |
|--------|-------------|----------|
| GAL Manufacturing | OP22-0002L | Elevator door operator arms |
| Global Industrial | 160CP19, 168255 | Rivet beams, noseplates |
| PartsTown | 810803, 1086700 | Commercial kitchen equipment |
| True Manufacturing | 810803 | Refrigerator door gaskets |
| Garland | 1086700 | Range burners |
| Hoshizaki | 4A2878-01 | Ice machine evaporators |
| Manitowoc | 000007965 | Ice thickness probes |
| Vulcan | 00-719255 | Thermostat knobs |

### Example: GAL Elevator Part Lookup

Input:
```
PART ID PART DESCRIPTION
OP22-0002L ARM ASSEMBLY, SS 25"-29" D.O.
```

Research Process:
1. Detect part number: `OP22-0002L`
2. Check built-in database → Found!
3. Retrieve catalog URL: `https://www.gal.com/wp-content/uploads/2023/07/VAN024_Print-and-Digital-Catalogue_06262023_final-1.pdf`
4. Extract dimensions:
   - Arm length range: 635mm - 736.6mm (25"-29")
   - Shaft diameter: 25.4mm (1")
   - Mounting hole: 12.7mm (1/2")
   - Wall thickness: 3.175mm (1/8")
5. Generate CAD entities with accurate dimensions

## Validation Tests

All mathematical implementations have been validated:

1. **Bezier Endpoint Interpolation**: Curve passes through P₀ at t=0 and Pₙ at t=1
2. **B-Spline Clamped Endpoints**: Clamped knot vector ensures endpoint interpolation
3. **NURBS Circle Accuracy**: Points on NURBS circle are within 0.000001 of true radius
4. **Polygon Area (Shoelace)**: Exact for convex and concave polygons
5. **Bezier Derivatives**: Tangent vectors computed correctly via hodograph
6. **BRep Loop Area**: Accurate area calculation for loops with curved edges

## CAD Compatibility

Generated DXF files use AutoCAD 2010 format (R2010) which supports:
- Native SPLINE entities (B-splines and NURBS)
- ELLIPSE entities
- LWPOLYLINE with bulge values

Compatible with:
- AutoCAD 2010+
- DraftSight
- LibreCAD
- FreeCAD
- QCAD
- Most CAD/CAM software
