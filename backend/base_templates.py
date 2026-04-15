"""Base Templates - Python-based non-ambiguous templates for quick starts."""

from typing import Dict, List, Any


class BaseTemplate:
    """Base class for predefined templates."""

    def __init__(self, name: str, category: str, description: str, prompt: str):
        self.name = name
        self.category = category
        self.description = description
        self.prompt = prompt

    def get_prompt(self) -> str:
        """Get the template prompt."""
        return self.prompt


# Residential Floor Plans
RESIDENTIAL_TEMPLATES: Dict[str, BaseTemplate] = {
    "studio_apartment": BaseTemplate(
        name="Studio Apartment (35m²)",
        category="residential",
        description="Efficient studio with combined living/sleeping, kitchenette, bathroom",
        prompt="""Create a professional studio apartment floor plan:
- Total area: 35m²
- Main room: 5000mm × 6000mm (combined living/sleeping)
- Kitchenette: 2500mm along wall with counter, sink, compact appliances
- Bathroom: 2000mm × 2000mm with toilet, sink, shower
- Entrance with closet
- Walls: 200mm (exterior), 150mm (bathroom)
- Doors: 900mm entrance, 800mm bathroom, with swing arcs
- Windows: 1200mm × 1200mm, multiple for light
- Include basic furniture to show space zoning
- Layers: Walls, Doors, Windows, Furniture, Fixtures"""
    ),

    "1br_apartment": BaseTemplate(
        name="1-Bedroom Apartment (50m²)",
        category="residential",
        description="Compact 1BR with living, kitchen, bathroom",
        prompt="""Create a professional 1-bedroom apartment floor plan:
- Total area: 50m²
- Bedroom: 3000mm × 3500mm with door and window
- Living room: 4000mm × 4000mm with windows
- Kitchen: 2500mm × 3000mm with counter space
- Bathroom: 2000mm × 2000mm with toilet, sink, shower
- Entrance hallway connecting rooms
- Walls: 200mm (exterior), 150mm (interior)
- Doors: 900mm standard, with swing arcs
- Windows: 1200mm × 1200mm with frames
- Layers: Walls, Doors, Windows"""
    ),

    "3br_house": BaseTemplate(
        name="3-Bedroom House (150m²)",
        category="residential",
        description="Family home with 3BR, 2 bathrooms, living, kitchen, dining",
        prompt="""Create a professional 3-bedroom house floor plan:
- Total area: 150m²
- Master bedroom: 4000mm × 3500mm with ensuite 2000mm × 2000mm
- Bedroom 2: 3000mm × 3000mm
- Bedroom 3: 3000mm × 3000mm
- Living room: 5000mm × 4000mm
- Kitchen: 3000mm × 3000mm with appliances
- Dining: 3000mm × 3000mm adjacent to kitchen
- Main bathroom: 2000mm × 2000mm
- Entrance hallway and circulation
- Walls: 200mm (exterior), 150mm (interior)
- Doors: 900mm (interior), 1000mm (front), with swings
- Windows: 1200mm × 1200mm standard, 1800mm × 1200mm (living)
- Layers: Walls, Doors, Windows, Fixtures"""
    ),
}


# Commercial Floor Plans
COMMERCIAL_TEMPLATES: Dict[str, BaseTemplate] = {
    "small_office": BaseTemplate(
        name="Small Office (100m²)",
        category="commercial",
        description="Office with 6 workstations, meeting room, reception",
        prompt="""Create a professional small office layout:
- Total area: 100m²
- Open workstations: 6 desks in open plan
- Meeting room: 3000mm × 4000mm with table and chairs
- Reception area: Desk and waiting area
- Break room: 3000mm × 3000mm with kitchenette
- Restroom: 2000mm × 3000mm
- Walls: 150mm (interior), 200mm (exterior)
- Doors: 900mm standard, 1000mm entrance
- Windows: Multiple along exterior
- Ceiling: 3000mm
- Layers: Walls, Doors, Windows, Furniture"""
    ),

    "retail_shop": BaseTemplate(
        name="Retail Shop (80m²)",
        category="commercial",
        description="Retail space with sales floor, storage, checkout",
        prompt="""Create a professional retail shop layout:
- Total area: 80m²
- Sales floor: 6000mm × 8000mm open space
- Checkout counter: 2000mm long at entrance
- Storage room: 3000mm × 3000mm at rear
- Fitting room: 1500mm × 1500mm (if applicable)
- Staff restroom: 1500mm × 2000mm
- Walls: 200mm (exterior), 150mm (interior)
- Entrance: 1200mm double door (accessibility)
- Display windows: Large 2400mm × 1200mm front windows
- Layers: Walls, Doors, Windows, Fixtures"""
    ),
}


# Industrial Templates
INDUSTRIAL_TEMPLATES: Dict[str, BaseTemplate] = {
    "small_warehouse": BaseTemplate(
        name="Small Warehouse (300m²)",
        category="industrial",
        description="Warehouse with loading dock, office, storage",
        prompt="""Create a professional small warehouse layout:
- Total area: 300m²
- Main warehouse: 15000mm × 20000mm open area
- Office: 4000mm × 4000mm with desks
- Loading dock: 2 bays, 3000mm wide each
- Storage racks: Marked rows in warehouse
- Restroom: 2000mm × 2000mm
- Walls: 200mm concrete (exterior), 150mm (office)
- Industrial doors: 3000mm (loading), 1000mm (personnel)
- Office windows: 1200mm × 1200mm
- Height: 6000mm (noted)
- Layers: Walls, Doors, Equipment"""
    ),
}


# Mechanical Parts
MECHANICAL_TEMPLATES: Dict[str, BaseTemplate] = {
    "gear_20t": BaseTemplate(
        name="Spur Gear (20 teeth)",
        category="mechanical",
        description="Small spur gear for light-duty applications",
        prompt="""Create a professional 20-tooth spur gear:
- Number of teeth: 20
- Module: 2mm
- Pitch diameter: 40mm
- Outer diameter: 44mm
- Root diameter: 35mm
- Bore: 10mm diameter
- Pressure angle: 20° (standard)
- Generate all circles (outer, pitch, root, bore)
- Generate tooth profiles: 20 evenly spaced
- Layers: Outlines, CenterLines
- Include center lines"""
    ),

    "bearing_6205": BaseTemplate(
        name="Ball Bearing (6205)",
        category="mechanical",
        description="Standard deep groove ball bearing",
        prompt="""Create a professional ball bearing 6205:
- Designation: 6205
- Bore (inner diameter): 25mm
- Outer diameter: 52mm
- Width: 15mm
- Ball pitch diameter: ~38.5mm (midpoint)
- Generate concentric circles (outer, ball pitch, bore)
- Section view representation
- Layers: Outlines, CenterLines
- Include dimensions"""
    ),

    "bolt_m8": BaseTemplate(
        name="Hex Bolt M8×40",
        category="mechanical",
        description="ISO metric M8 hex head bolt, 40mm length",
        prompt="""Create a professional M8 hex bolt:
- Size: M8 (8mm nominal diameter)
- Length: 40mm total
- Hex head: 13mm across flats, 5.5mm height
- Generate hexagonal head (6-point closed polyline)
- Generate shank as circle (8mm diameter, top view)
- Thread representation: simplified
- Layers: Outlines, CenterLines
- Include dimensions"""
    ),
}


# All templates combined
ALL_TEMPLATES: Dict[str, BaseTemplate] = {
    **RESIDENTIAL_TEMPLATES,
    **COMMERCIAL_TEMPLATES,
    **INDUSTRIAL_TEMPLATES,
    **MECHANICAL_TEMPLATES,
}


def get_template(template_name: str) -> BaseTemplate:
    """Get a template by name."""
    return ALL_TEMPLATES.get(template_name)


def list_templates(category: str = None) -> List[Dict[str, str]]:
    """
    List all templates, optionally filtered by category.

    Args:
        category: Optional category filter (residential, commercial, industrial, mechanical)

    Returns:
        List of template info dicts
    """
    templates = ALL_TEMPLATES.values()

    if category:
        templates = [t for t in templates if t.category == category]

    return [
        {
            "name": t.name,
            "category": t.category,
            "description": t.description
        }
        for t in templates
    ]


def list_categories() -> List[str]:
    """List all available template categories."""
    categories = set(t.category for t in ALL_TEMPLATES.values())
    return sorted(categories)


def get_templates_by_category(category: str) -> Dict[str, BaseTemplate]:
    """Get all templates in a specific category."""
    if category == "residential":
        return RESIDENTIAL_TEMPLATES
    elif category == "commercial":
        return COMMERCIAL_TEMPLATES
    elif category == "industrial":
        return INDUSTRIAL_TEMPLATES
    elif category == "mechanical":
        return MECHANICAL_TEMPLATES
    else:
        return {}
