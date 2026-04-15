#!/usr/bin/env python3
"""
Advanced automated test script for DXF Generator chatbot.
Tests challenging prompts with detailed specifications and multi-turn conversations.
Designed to stress-test the system and find edge cases.
"""

import requests
import time
import json
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

BASE_URL = "http://localhost:5001"


@dataclass
class ConversationTest:
    """A multi-turn conversation test case."""
    name: str
    description: str
    messages: List[str]  # List of messages in order (alternating user inputs)
    expected_issues: List[str] = field(default_factory=list)  # Known potential issues


# Advanced test cases with detailed numerical specifications
ADVANCED_TESTS: List[ConversationTest] = [
    # Test 1: Extremely detailed warehouse with conflicting dimensions
    ConversationTest(
        name="Detailed Warehouse with Conflicts",
        description="Tests handling of very specific but potentially conflicting dimensions",
        messages=[
            """Design a warehouse facility with the following exact specifications:
            - Main building: 75.5m x 42.3m footprint, 12m ceiling height
            - 6 loading docks on the east wall, each 3.5m wide x 4.2m tall, spaced 5m apart starting 8m from the north corner
            - Office area in the northwest corner: 15m x 10m with 3m ceiling (mezzanine level at 3m)
            - 4 rows of storage shelving, each row 60m long, 2.4m wide, spaced 4m apart
            - Main entrance on south wall: double door 2.4m wide x 3m tall, centered
            - Emergency exits: 4 total, 1.2m wide each, located at each corner
            - Support columns: 0.5m x 0.5m, grid of 6x4 columns spaced evenly
            - Forklift charging station in southeast corner: 8m x 5m area""",
            # Follow-up with corrections
            "The loading docks should actually be 4m wide not 3.5m, and there should be 8 docks not 6. Also add a truck turning radius guide of 12m outside each dock.",
            # Follow-up with additions
            "Add fire suppression system markers every 10m along the ceiling grid. Also include 3 floor drains - one in the center and two near the loading docks.",
        ],
        expected_issues=["dimension conflicts", "spacing calculations", "overlapping elements"]
    ),

    # Test 2: Complex mechanical assembly with precise tolerances
    ConversationTest(
        name="Precision Gearbox Assembly",
        description="Tests handling of precise mechanical tolerances and assemblies",
        messages=[
            """Draw a 3-stage reduction gearbox with these specifications:
            - Input shaft: 25mm diameter, 150mm length, keyway 8mm x 4mm x 40mm
            - Stage 1: 20-tooth pinion (module 2.5) driving 80-tooth gear, center distance 125mm
            - Stage 2: 18-tooth pinion (module 3) driving 72-tooth gear, center distance 135mm
            - Stage 3: 16-tooth pinion (module 4) driving 64-tooth gear, center distance 160mm
            - Output shaft: 50mm diameter, 200mm length, keyway 14mm x 5.5mm x 70mm
            - Bearing housings: 6205 bearings (25mm bore) for input, 6210 bearings (50mm bore) for output
            - Housing wall thickness: 12mm, total housing size approximately 400mm x 300mm x 250mm
            - All gears 20° pressure angle, face width 30mm for stage 1, 40mm for stage 2, 50mm for stage 3
            - Include oil drain plug M16x1.5 at lowest point and oil fill port M20x1.5 at top""",
            # Follow-up questioning the math
            "Wait, check the center distances - for module 2.5 with 20 and 80 teeth, shouldn't the center distance be (20+80)*2.5/2 = 125mm? That's correct. But for module 3 with 18+72 teeth it should be 135mm. And module 4 with 16+64 = 160mm. Confirm these are drawn correctly.",
            # Follow-up with additional features
            "Add inspection covers on both sides, 100mm x 80mm with 6x M6 bolt holes on a 90mm x 70mm pattern. Also show the gear mesh contact patterns.",
        ],
        expected_issues=["gear tooth calculations", "center distance validation", "tolerance stacking"]
    ),

    # Test 3: Architectural floor plan with impossible constraints
    ConversationTest(
        name="Impossible Floor Plan",
        description="Tests handling of physically impossible or contradictory requirements",
        messages=[
            """Create a residential floor plan with these requirements:
            - Total area exactly 120 square meters in a 10m x 12m rectangle
            - Master bedroom: 25 sqm with ensuite bathroom 8 sqm and walk-in closet 6 sqm
            - Second bedroom: 16 sqm
            - Third bedroom: 14 sqm
            - Living room: 35 sqm (must be open plan with kitchen)
            - Kitchen: 15 sqm
            - Main bathroom: 6 sqm
            - Hallway/circulation: 12 sqm
            - Laundry: 4 sqm
            - Storage closet: 3 sqm
            - All rooms must have at least one window (minimum 1.2m wide)
            - All doorways 900mm wide, all interior walls 150mm thick
            - Master bedroom must be isolated from other bedrooms by living area""",
            # Point out the math doesn't add up
            "I just calculated - that's 25+8+6+16+14+35+15+6+12+4+3 = 144 sqm of rooms but only 120 sqm total. How did you handle this? The walls take up space too.",
            # Request specific room placement
            "Put the master suite in the southeast corner, living/kitchen along the entire north wall, and stack the two other bedrooms on the west wall. Show me the dimensions of each room.",
        ],
        expected_issues=["area calculations don't fit", "wall thickness eating space", "impossible layout"]
    ),

    # Test 4: Complex piping system with flow calculations
    ConversationTest(
        name="Industrial Piping Network",
        description="Tests complex interconnected systems with specific routing",
        messages=[
            """Design a chemical plant piping system:
            - Main header: 8-inch Schedule 40 pipe (ID 202.7mm, OD 219.1mm), running 25m east-west at elevation 5m
            - 6 branch takeoffs from header: 4-inch Schedule 40 (ID 102.3mm), dropping vertically to equipment at elevation 1m
            - Branch spacing: first at 2m from west end, then at 5m intervals
            - Each branch has a gate valve (4-inch, face-to-face 178mm) at the top and a control valve (4-inch, face-to-face 292mm) at elevation 3m
            - 90° long-radius elbows at all direction changes (4-inch LR elbow center-to-face 152mm)
            - Expansion loop in main header at center: 2m x 1m rectangular loop using 8-inch pipe
            - Flanged connections at all valves: ANSI 150# raised face (4-inch flange OD 228.6mm, 8 bolt holes)
            - Drain valves: 1-inch at low points of each branch
            - Vent valves: 3/4-inch at high points
            - Pipe supports every 3m maximum span""",
            # Question about specific routing
            "For branch 3 (at 12m from west), I need it to route around an obstruction. Add two 45° elbows to offset the pipe 500mm to the north between elevations 4m and 3.5m, then back to the original centerline.",
            # Add instrumentation
            "Add flow meters on branches 1, 3, and 5. Use orifice plates with flange taps, plate bore 65mm, beta ratio 0.637. Also add pressure gauges before each control valve and temperature elements after each control valve.",
        ],
        expected_issues=["3D elevation handling", "pipe routing conflicts", "instrument placement"]
    ),

    # Test 5: Spacecraft with precise module dimensions
    ConversationTest(
        name="Modular Space Station",
        description="Tests handling of modular assemblies with docking interfaces",
        messages=[
            """Design a modular space station with these components:
            - Core module: cylindrical, 4.5m diameter x 12m length, 6mm wall thickness aluminum
            - 4 radial docking ports at 90° intervals, 3m from each end, using Common Berthing Mechanism (CBM) - 127cm diameter
            - 2 axial docking ports (one each end) using Androgynous Peripheral Attach System (APAS) - 80cm inner diameter
            - Solar array truss: 8m long x 0.5m diameter, attached to port 1, with 4 solar panels each 2.4m x 6m
            - Laboratory module on port 2: 4.5m diameter x 8m length, 3 experiment racks (2m x 1m x 0.6m each)
            - Habitation module on port 3: 4.5m diameter x 10m length, includes 4 crew quarters (2m x 2m x 2.2m each)
            - Logistics module on port 4: 4.5m diameter x 6m length, pressurized cargo volume 35 cubic meters
            - Cupola on nadir port of core: 7 windows, 80cm diameter each, arranged hexagonally with center window
            - Radiator panels: 2 per module, 3m x 6m each, mounted on rotating joints""",
            # Clarify docking orientation
            "I need the laboratory module rotated 15° around its long axis relative to the core module so the experiment rack access faces the cupola side. Also, the APAS ports should have 12 guide petals visible.",
            # Add internal details
            "Inside the habitation module, add the crew quarters layout with each quarter having a 60cm x 80cm sleeping bag wall mount, a 40cm x 30cm personal storage compartment, and a 20cm x 20cm ventilation grille. Include the connecting tunnel dimensions - 1.2m diameter.",
        ],
        expected_issues=["circular geometry precision", "3D orientation", "interface compatibility"]
    ),

    # Test 6: Gothic cathedral with complex geometry
    ConversationTest(
        name="Gothic Cathedral Floor Plan",
        description="Tests complex architectural curves and symmetry",
        messages=[
            """Create a Gothic cathedral floor plan:
            - Total length: 120m, maximum width at transept: 45m
            - Nave: 75m long x 15m wide, 8 bays with columns at 9.375m spacing
            - Side aisles: 6m wide each, flanking the nave
            - Transept: 45m total width x 12m deep, crossing at 60m from west entrance
            - Choir: 25m long x 12m wide, east of crossing
            - Apse: semicircular, 12m diameter, with 5 radiating chapels each 4m wide x 6m deep
            - Ambulatory: 3m wide, wrapping around choir and apse
            - West facade: twin towers, each 8m x 8m, flanking a 6m wide central portal
            - Flying buttress positions: 12 per side, aligned with nave columns
            - Rose window locations: west facade (10m diameter), north and south transept (8m diameter each)
            - Column dimensions: nave columns 1.8m diameter, aisle columns 1.2m diameter
            - Wall thickness: exterior 2m, interior 0.8m""",
            # Request specific details
            "For the radiating chapels in the apse, they should have pointed arch entrances (ogival arches) with a height-to-width ratio of 2:1. The chapel at the center axis should be larger - 5m wide x 8m deep - as the Lady Chapel.",
            # Add more elements
            "Add the crypt level below the choir - same footprint as choir and apse above, with 20 support columns in a 4x5 grid. Include two spiral staircases (1.5m outer diameter, 0.3m central column) connecting nave level to crypt, located in the corners where transept meets choir.",
        ],
        expected_issues=["semicircular calculations", "radiating geometry", "symmetry maintenance"]
    ),

    # Test 7: Electronic enclosure with precise cutouts
    ConversationTest(
        name="Precision Electronics Enclosure",
        description="Tests precise rectangular cutouts and mounting patterns",
        messages=[
            """Design a 19-inch rack-mount electronics enclosure:
            - Overall: 482.6mm wide (19") x 266.7mm high (6U) x 450mm deep
            - Front panel: 2mm thick aluminum, with these cutouts:
              * LCD display window: 147.32mm x 110.49mm, centered horizontally, top edge 40mm from top
              * 16 LED indicators: 5mm diameter holes in 2 rows of 8, 10mm spacing, starting 30mm from left edge, 180mm from top
              * 4 pushbuttons: 12mm diameter holes, horizontal row at 220mm from top, at x=60, 120, 362, 422mm
              * Ventilation: 80 slots, 2mm x 20mm each, in 10x8 grid with 3mm spacing, lower right area
              * DB-25 connector: 47.04mm x 12.55mm rectangular cutout with 2x M3 mounting holes on 33.32mm spacing
              * USB-A ports: 3x cutouts 13.14mm x 5.71mm, horizontal spacing 20mm, starting at x=200mm, y=200mm
            - Side panels: 1.5mm steel, 10 horizontal ventilation louvers each side (100mm x 3mm, 15mm spacing)
            - Rear panel: 2mm aluminum
              * IEC power inlet: 27.5mm x 19.5mm cutout with M3 mounting holes
              * 2x Ethernet RJ45: 15.24mm x 13.34mm each
              * 40mm fan cutout with guard mounting holes (4x M4 on 32mm diagonal pattern)
            - Internal standoffs for PCB mounting: M3, 8mm height, at coordinates (50,50), (150,50), (250,50), (350,50), (50,180), (150,180), (250,180), (350,180) from front-left-bottom""",
            # Corrections
            "The LED holes should be 3mm not 5mm for standard 3mm LEDs. Also add light pipes - each needs a 3.2mm counterbore, 5mm diameter, 1mm deep on the inside surface. And the LCD cutout needs corner radius of 2mm.",
            # Additional requirements
            "Add EMI/RFI shielding considerations: the ventilation slots need to be max 3mm wide (change from current 2mm x 20mm to 3mm x 15mm), add a continuous EMI gasket groove (2mm wide x 2mm deep) around the front panel perimeter 5mm from edge, and add ground lug mounting point (M4, 10mm from bottom-right corner of rear panel).",
        ],
        expected_issues=["precise decimal dimensions", "overlapping cutouts", "tolerance accumulation"]
    ),

    # Test 8: Hydraulic circuit with specific component sizes
    ConversationTest(
        name="Hydraulic Press Circuit",
        description="Tests schematic-style drawings with specific component representations",
        messages=[
            """Draw a hydraulic circuit for a 100-ton press:
            - Reservoir: 500 liter capacity, shown as 800mm x 800mm rectangle with level gauge and breather
            - Main pump: variable displacement axial piston, 100 cc/rev, 1800 RPM, inlet filter 125 micron
            - System pressure: 250 bar max, set by main relief valve
            - Main cylinder: 200mm bore x 150mm stroke, single-acting with gravity return
            - Pilot operated check valve on cylinder port (to hold load)
            - 4/3 directional control valve: solenoid operated, spring centered, tandem center
            - Pressure reducing valve for clamping circuit: set at 80 bar
            - Clamp cylinders: 2x 63mm bore x 50mm stroke
            - Flow control valve with check bypass for speed control
            - Pressure gauge ports: before and after each valve, 1/4" NPT
            - Filter: 10 micron return line filter with bypass indicator
            - Cooler: air-oil type, in return line, 15 kW capacity
            - Line sizes: pressure lines 1" tube, return lines 1.5" tube, drain lines 1/2" tube
            - Use ISO 1219 symbols for all components""",
            # Ask for modifications
            "Add accumulator charging circuit: 20 liter bladder accumulator pre-charged to 90 bar, with needle valve isolation block and pressure transducer. Position it between the pump and main directional valve.",
            # Request specific symbol details
            "For the directional valve symbol, show all 4 envelope positions clearly with the flow path arrows. The P-to-A and B-to-T paths in one position, P-to-B and A-to-T in another, and both P and T blocked with A and B interconnected in center. Include the solenoid coils labeled Y1 and Y2.",
        ],
        expected_issues=["symbol representation", "circuit connectivity", "component spacing"]
    ),

    # Test 9: Extremely precise surveying/land plot
    ConversationTest(
        name="Complex Land Survey Plot",
        description="Tests handling of bearing/distance notation and closure calculations",
        messages=[
            """Create a land survey plot with these boundary calls:
            Starting at Point of Beginning (POB) marked by iron pin:
            - N 15°32'45" E, 234.56 feet to iron pin
            - N 78°14'22" E, 156.78 feet to concrete monument
            - S 45°00'00" E, 312.89 feet to iron pin in concrete
            - Along a curve to the right with radius 500.00 feet, arc length 245.67 feet, chord bearing S 30°45'15" E, chord length 242.34 feet to iron pin
            - S 12°18'33" W, 445.12 feet to iron pin
            - N 85°42'18" W, 523.45 feet to iron pin
            - Along a curve to the left with radius 350.00 feet, arc length 178.23 feet to iron pin
            - N 05°15'00" W, 289.34 feet back to POB

            Include:
            - All bearing labels with degree/minute/second notation
            - All distance labels in feet with 2 decimal places
            - Curve data tables showing radius, arc, chord, chord bearing
            - Iron pin symbols (circle with X) and monument symbols (square)
            - North arrow with magnetic declination 5°30' W
            - Scale bar for 1"=100' scale
            - Total calculated area in square feet and acres
            - Closure error if any (should close within 1:10,000)""",
            # Check the math
            "Calculate the closure - does this traverse actually close? What's the error of closure? If it doesn't close exactly, show me the misclosure vector.",
            # Add easements
            "Add a 30-foot utility easement along the entire north boundary, a 15-foot drainage easement along the curve on the east side, and a 60-foot road right-of-way along the south boundary. Show these with dashed lines and hatch patterns. Also add the setback lines - 25 feet from all property boundaries.",
        ],
        expected_issues=["trigonometric calculations", "closure errors", "curve calculations"]
    ),

    # Test 10: Failed geometry edge cases
    ConversationTest(
        name="Geometry Edge Cases",
        description="Tests handling of degenerate and edge-case geometry",
        messages=[
            """Create a test drawing with these specific geometric edge cases:
            - A line from (0,0) to (0,0) - zero length line
            - A circle with radius 0 at point (100, 100)
            - A circle with radius -50 at point (200, 200)
            - An arc from 0° to 360° with radius 30 at (300, 300) - full circle as arc
            - An arc from 45° to 45° with radius 25 at (400, 400) - zero sweep arc
            - An arc with negative radius -40, from 0° to 90° at (500, 500)
            - A polyline with only one point at (600, 600)
            - A polyline with duplicate consecutive points: (700,700), (700,700), (750,750), (750,750), (700,700)
            - A self-intersecting polyline: (0,500), (100,500), (50,450), (50,550), (0,500)
            - Overlapping lines: line from (800,0) to (900,0) and line from (850,0) to (950,0)
            - Coincident circles: both radius 25 at point (1000, 1000)
            - A rectangle specified as polyline with floating point precision: (0.1+0.2, 0), (0.3, 100.00000001), (0, 99.99999999), (0, 0)""",
            # Ask how it handled them
            "Which of these did you reject, which did you fix automatically, and which did you draw as-is? Explain each decision.",
            # Push for the actual output
            "Show me the actual CSV output you generated, including any warnings or modifications you made to the geometry.",
        ],
        expected_issues=["zero-length entities", "negative dimensions", "degenerate geometry", "floating point precision"]
    ),

    # Test 11: Very large scale with very small details
    ConversationTest(
        name="Multi-Scale Airport Layout",
        description="Tests handling of extreme scale differences in same drawing",
        messages=[
            """Design an airport layout with both macro and micro details:

            MACRO SCALE (full airport):
            - Main runway 09/27: 3500m x 45m, heading 090°/270°
            - Crosswind runway 18/36: 2800m x 40m, heading 180°/360°
            - Taxiways: 23m wide, connecting runways to terminal
            - Terminal building footprint: 400m x 80m
            - Cargo area: 200m x 150m
            - Control tower location: 100m south of terminal center
            - Parking apron: 500m x 200m

            MICRO SCALE (terminal detail):
            - 20 aircraft gates, each gate 50m frontage
            - Jet bridges: 6m wide x 15m long each
            - Gate door dimensions: 2.4m wide x 2.5m high
            - Seating areas: rows of 5 seats, seat width 0.5m, row spacing 1.2m
            - Check-in counters: 1.2m wide x 0.8m deep each, 40 total in 2 rows
            - Baggage carousel: 30m oval, 1.5m wide belt
            - Individual floor tiles in terminal: 0.6m x 0.6m (show grid in check-in area only)

            DETAIL SCALE (control tower):
            - Tower height: 45m, cab diameter: 12m
            - Window frames: 50mm wide mullions
            - Equipment rack: 600mm x 800mm standard server rack
            - Individual control buttons: 15mm diameter""",
            # Question the scale handling
            "How are you handling the scale difference between a 3.5km runway and 15mm buttons? That's a 1:233,333 ratio. What's the smallest feature you can represent?",
            # Request specific area detail
            "Zoom into just the check-in area and show me the floor tile grid, counter positions with dimensions, and queuing barrier layouts (retractable belt barriers, 2m spacing between posts).",
        ],
        expected_issues=["extreme scale ratios", "precision limits", "level of detail handling"]
    ),

    # Test 12: Recursive/fractal-like geometry
    ConversationTest(
        name="Fractal Antenna Pattern",
        description="Tests handling of recursive geometric patterns",
        messages=[
            """Create a Sierpinski gasket fractal antenna pattern with these specifications:
            - Base equilateral triangle: 100mm side length
            - Iterate to level 5 (5 levels of subdivision)
            - Level 0: single triangle, vertices at (0,0), (100,0), (50, 86.6)
            - Level 1: remove center triangle, leaving 3 triangles each 50mm side
            - Level 2: each of 3 triangles subdivided, 9 triangles of 25mm side
            - Level 3: 27 triangles of 12.5mm side
            - Level 4: 81 triangles of 6.25mm side
            - Level 5: 243 triangles of 3.125mm side

            Additional requirements:
            - Feed point at bottom center vertex
            - 50-ohm microstrip feed line: 3.1mm wide x 20mm long
            - Ground plane: 120mm x 120mm rectangle behind antenna
            - Substrate outline: 110mm x 110mm, centered on pattern
            - Corner mounting holes: 3mm diameter, 5mm from corners
            - All triangle edges should be 0.5mm wide copper traces""",
            # Verify the count
            "That should be 1+3+9+27+81+243 = 364 triangles total if I count the hierarchy, but actually Sierpinski only keeps 243 at level 5. Verify you have exactly 243 triangles drawn, each with 3 sides = 729 line segments.",
            # Request DRC check
            "Check the minimum spacing between any two non-connected traces. At level 5 with 3.125mm triangles and 0.5mm trace width, what's the actual gap? Is it manufacturable? Flag any spacing violations under 0.2mm.",
        ],
        expected_issues=["recursive generation", "very high entity count", "precision at small scales"]
    ),
]


class AdvancedChatbotTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    def check_server(self) -> bool:
        """Check if the server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def send_chat(self, message: str, session_id: str, is_followup: bool = False) -> Dict[str, Any]:
        """Send a chat message to the chatbot."""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": message,
                    "session_id": session_id,
                    "settings": {
                        "auto_accept_mode": False,  # Don't auto-accept so we see validation issues
                        "quality_level": "professional"
                    },
                    "is_refinement": is_followup
                },
                timeout=180  # Allow up to 3 minutes for complex prompts
            )
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timed out after 180 seconds"}
        except requests.exceptions.ConnectionError as e:
            return {"error": f"Connection error: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def run_conversation_test(self, test: ConversationTest) -> Dict[str, Any]:
        """Run a multi-turn conversation test."""
        session_id = f"advtest_{test.name.lower().replace(' ', '_').replace('/', '_')}_{int(time.time())}"

        print(f"\n{'='*70}")
        print(f"TEST: {test.name}")
        print(f"{'='*70}")
        print(f"Description: {test.description}")
        print(f"Session ID: {session_id}")
        print(f"Expected issues: {', '.join(test.expected_issues) if test.expected_issues else 'None specified'}")
        print(f"Number of turns: {len(test.messages)}")

        test_result = {
            "name": test.name,
            "description": test.description,
            "session_id": session_id,
            "expected_issues": test.expected_issues,
            "turns": [],
            "success": True,
            "total_time": 0,
            "final_state": None
        }

        for turn_num, message in enumerate(test.messages, 1):
            print(f"\n{'-'*70}")
            print(f"Turn {turn_num}/{len(test.messages)}")
            print(f"{'-'*70}")
            print(f"User: {message[:100]}{'...' if len(message) > 100 else ''}")

            start_time = time.time()
            is_followup = turn_num > 1
            result = self.send_chat(message, session_id, is_followup)
            elapsed_time = time.time() - start_time
            test_result["total_time"] += elapsed_time

            turn_result = {
                "turn": turn_num,
                "message": message,
                "elapsed_time": elapsed_time,
                "success": "error" not in result,
                "response": result
            }

            if "error" in result:
                print(f"ERROR: {result['error']}")
                turn_result["error"] = result["error"]
                test_result["success"] = False
            else:
                print(f"Response time: {elapsed_time:.2f}s")

                # Extract assistant response
                if "messages" in result:
                    for msg in result["messages"]:
                        if msg.get("role") == "assistant":
                            response_preview = msg.get("content", "")[:200]
                            print(f"Assistant: {response_preview}{'...' if len(msg.get('content', '')) > 200 else ''}")

                # Check for validation issues
                if "metadata" in result and "validation" in result["metadata"]:
                    validation = result["metadata"]["validation"]
                    is_valid = validation.get("is_valid", True)
                    confidence = validation.get("confidence_score", 0)
                    issues = validation.get("issues", [])

                    print(f"Validation: valid={is_valid}, confidence={confidence}")

                    if issues:
                        print(f"Validation issues ({len(issues)}):")
                        for issue in issues[:3]:
                            print(f"  ! {issue[:80]}{'...' if len(issue) > 80 else ''}")
                        if len(issues) > 3:
                            print(f"  ... and {len(issues) - 3} more")
                        turn_result["validation_issues"] = issues

                # Check entity counts
                if "metadata" in result and "entities" in result["metadata"]:
                    entities = result["metadata"]["entities"]
                    counts = {}
                    for k, v in entities.items():
                        if isinstance(v, list):
                            counts[k] = len(v)
                        elif isinstance(v, str) and k == "notes":
                            continue
                        else:
                            counts[k] = v
                    if counts:
                        print(f"Entities: {counts}")
                        turn_result["entity_counts"] = counts

                # Check if requires feedback
                if result.get("requires_feedback"):
                    print("Status: Requires user feedback")
                    if "questions" in result.get("metadata", {}).get("validation", {}):
                        questions = result["metadata"]["validation"]["questions"]
                        print(f"Questions: {questions[:2]}...")
                elif result.get("can_generate"):
                    print("Status: Ready to generate DXF")
                else:
                    print("Status: Processing...")

            test_result["turns"].append(turn_result)

            # If there was an error, stop the conversation
            if not turn_result["success"]:
                break

            # Brief pause between turns
            time.sleep(0.5)

        # Store final state
        if test_result["turns"] and test_result["turns"][-1].get("success"):
            test_result["final_state"] = test_result["turns"][-1].get("response", {})

        # Summary for this test
        print(f"\n{'~'*70}")
        print(f"Test Summary: {test.name}")
        print(f"Total time: {test_result['total_time']:.2f}s")
        print(f"Turns completed: {len([t for t in test_result['turns'] if t['success']])}/{len(test.messages)}")
        print(f"Overall success: {'PASS' if test_result['success'] else 'FAIL'}")

        self.results.append(test_result)
        return test_result

    def run_all_tests(self, test_indices: Optional[List[int]] = None) -> None:
        """Run all or selected test cases."""
        print("\n" + "=" * 70)
        print("DXF Generator Chatbot - Advanced Test Suite")
        print("=" * 70)

        # Check server first
        print("\nChecking server availability...")
        if not self.check_server():
            print(f"ERROR: Server not available at {self.base_url}")
            print("Please start the server first with: python -m backend.server")
            sys.exit(1)
        print(f"Server is running at {self.base_url}")

        # Select tests to run
        tests_to_run = ADVANCED_TESTS
        if test_indices:
            tests_to_run = [ADVANCED_TESTS[i] for i in test_indices if i < len(ADVANCED_TESTS)]
            print(f"\nRunning {len(tests_to_run)} selected tests")
        else:
            print(f"\nRunning all {len(tests_to_run)} tests")

        # Run tests
        for test in tests_to_run:
            self.run_conversation_test(test)
            time.sleep(2)  # Pause between tests

        # Print final summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print comprehensive test summary."""
        print("\n" + "=" * 70)
        print("FINAL TEST SUMMARY")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed

        print(f"\nTotal tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass rate: {100*passed/total:.1f}%" if total > 0 else "N/A")

        total_time = sum(r["total_time"] for r in self.results)
        print(f"Total time: {total_time:.2f}s")

        print("\n" + "-" * 70)
        print("Detailed Results:")
        print("-" * 70)

        for r in self.results:
            status = "PASS" if r["success"] else "FAIL"
            turns_completed = len([t for t in r["turns"] if t["success"]])
            total_turns = len(r["turns"])

            # Count validation issues across all turns
            total_issues = 0
            for turn in r["turns"]:
                total_issues += len(turn.get("validation_issues", []))

            print(f"\n[{status}] {r['name']}")
            print(f"      Time: {r['total_time']:.2f}s | Turns: {turns_completed}/{total_turns} | Validation issues: {total_issues}")

            if not r["success"]:
                for turn in r["turns"]:
                    if "error" in turn:
                        print(f"      Error (turn {turn['turn']}): {turn['error'][:60]}...")
                        break

            # Show sample of validation issues found
            all_issues = []
            for turn in r["turns"]:
                all_issues.extend(turn.get("validation_issues", []))
            if all_issues:
                print(f"      Sample issues:")
                for issue in all_issues[:2]:
                    print(f"        - {issue[:70]}{'...' if len(issue) > 70 else ''}")

        print("\n" + "=" * 70)

        # Save detailed results to file
        timestamp = int(time.time())
        results_file = f"advanced_test_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"Full results saved to: {results_file}")

        # Also save a simpler summary
        summary_file = f"advanced_test_summary_{timestamp}.txt"
        with open(summary_file, "w") as f:
            f.write("DXF Generator Advanced Test Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total: {total} | Passed: {passed} | Failed: {failed}\n")
            f.write(f"Pass rate: {100*passed/total:.1f}%\n" if total > 0 else "Pass rate: N/A\n")
            f.write(f"Total time: {total_time:.2f}s\n\n")
            for r in self.results:
                status = "PASS" if r["success"] else "FAIL"
                f.write(f"[{status}] {r['name']} ({r['total_time']:.2f}s)\n")
        print(f"Summary saved to: {summary_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced DXF Generator Chatbot Tester")
    parser.add_argument("--tests", type=str, help="Comma-separated list of test indices to run (0-based)")
    parser.add_argument("--list", action="store_true", help="List all available tests")
    parser.add_argument("--url", type=str, default=BASE_URL, help=f"Server URL (default: {BASE_URL})")

    args = parser.parse_args()

    if args.list:
        print("Available tests:")
        for i, test in enumerate(ADVANCED_TESTS):
            print(f"  {i}: {test.name}")
            print(f"     {test.description}")
            print(f"     Turns: {len(test.messages)}")
        return

    test_indices = None
    if args.tests:
        test_indices = [int(x.strip()) for x in args.tests.split(",")]

    tester = AdvancedChatbotTester(base_url=args.url)
    tester.run_all_tests(test_indices=test_indices)


if __name__ == "__main__":
    main()
