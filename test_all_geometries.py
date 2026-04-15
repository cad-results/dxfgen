#!/usr/bin/env python
"""
Comprehensive test for DXF generation with all supported geometry types.
Tests: Lines (L), Circles (C), Arcs (A), Polylines (P), and Hatches (H)
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dxf_generator import DXFGenerator


def test_all_geometries():
    """Test DXF generation with all supported geometry types."""

    # Comprehensive test data with all geometry types
    test_data = """L,Square,1,LINES
0,0
10,0
10,10
0,10
0,0

C,Circles,1,CIRCLES
5,5,2
15,5,3

A,Arcs,1,ARCS
25,5,4,0,90
35,5,3,45,180
45,5,2,0,270

P,Polyline,1,POLYLINES
55,0,0,0,0
60,0,0.5,0.5,0
65,5,0.5,0.5,0.5
70,5,0,0,0

H,Hatch,1,HATCHES
75,0,0
80,0,0
80,5,0
75,5,0
75,0,0
"""

    print("Testing DXF generation with all geometry types...")
    print("=" * 60)

    # Initialize generator
    try:
        generator = DXFGenerator()
        print(f"✓ DXF Generator initialized")
        print(f"  text_to_dxf path: {generator.text_to_dxf_path}")
    except Exception as e:
        print(f"✗ Failed to initialize generator: {e}")
        return False

    # Generate DXF
    print("\nGenerating DXF file...")
    success, output_path, error_msg = generator.generate(
        test_data,
        "test_all_geometries.dxf"
    )

    if success:
        print(f"✓ DXF file generated successfully!")
        print(f"  Output: {output_path}")

        # Verify file exists and has content
        output_file = Path(output_path)
        if output_file.exists():
            size = output_file.stat().st_size
            print(f"  File size: {size} bytes")

            # Basic validation - check if file contains expected sections
            with open(output_path, 'r') as f:
                content = f.read()

            checks = {
                "DXF header": "HEADER" in content,
                "Entities section": "ENTITIES" in content,
                "Lines": "LINE" in content,
                "Circles": "CIRCLE" in content,
                "Arcs": "ARC" in content,
                "Polylines": "LWPOLYLINE" in content,
                "Hatches": "HATCH" in content,
            }

            print("\nContent validation:")
            all_passed = True
            for check_name, passed in checks.items():
                status = "✓" if passed else "✗"
                print(f"  {status} {check_name}")
                if not passed:
                    all_passed = False

            return all_passed
        else:
            print(f"✗ Output file does not exist: {output_path}")
            return False
    else:
        print(f"✗ DXF generation failed!")
        print(f"  Error: {error_msg}")
        return False


def test_individual_geometries():
    """Test each geometry type individually."""

    test_cases = {
        "Lines": """L,Line Test,1,LAYER1
0,0
10,10
20,0

""",
        "Circles": """C,Circle Test,1,LAYER1
10,10,5
25,10,8

""",
        "Arcs": """A,Arc Test,1,LAYER1
10,10,5,0,180

""",
        "Polylines": """P,Polyline Test,1,LAYER1
0,0,0,0,0
10,0,0,0,0
10,10,0,0,0
0,10,0,0,0

""",
        "Hatches": """H,Hatch Test,1,LAYER1
0,0,0
10,0,0
10,10,0
0,10,0
0,0,0

"""
    }

    print("\n" + "=" * 60)
    print("Testing individual geometry types...")
    print("=" * 60)

    generator = DXFGenerator()
    results = {}

    for name, data in test_cases.items():
        print(f"\nTesting {name}...")
        success, output_path, error_msg = generator.generate(
            data,
            f"test_{name.lower()}.dxf"
        )

        if success:
            print(f"  ✓ {name} test passed")
            print(f"    Output: {output_path}")
            results[name] = True
        else:
            print(f"  ✗ {name} test failed")
            print(f"    Error: {error_msg}")
            results[name] = False

    return results


if __name__ == "__main__":
    print("DXF Generation Comprehensive Test")
    print("=" * 60)

    # Test all geometries together
    all_test_passed = test_all_geometries()

    # Test individual geometries
    individual_results = test_individual_geometries()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"All geometries test: {'PASSED' if all_test_passed else 'FAILED'}")
    print("\nIndividual geometry tests:")
    for name, passed in individual_results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {name}: {status}")

    # Overall result
    all_passed = all_test_passed and all(individual_results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
