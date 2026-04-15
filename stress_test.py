#!/usr/bin/env python3
"""
Comprehensive stress test for DXF Generator Chatbot.
Tests various query types with different toggle combinations.
"""

import requests
import json
import time
import sys
import traceback
from typing import Dict, List, Any, Tuple
from itertools import product


BASE_URL = "http://localhost:5001"


# Test queries organized by category
TEST_QUERIES = {
    "simple_shapes": [
        "draw a rectangle 100x50mm",
        "create a circle with radius 25mm",
        "make a simple triangle",
        "",  # Empty query - should error gracefully
        "   ",  # Whitespace only - should error gracefully
    ],
    "vague_architectural": [
        "build a house",
        "create an apartment",
        "design an office space",
        "make a small cabin",
    ],
    "detailed_architectural": [
        "3-bedroom house with master bedroom 4m x 3.5m, two bedrooms 3m x 3m each, 2 bathrooms 2m x 2m, living room 5m x 4m, kitchen 3m x 3m",
        "2-bedroom apartment 50sqm with living room, kitchen, and bathroom",
        "small office with 3 workstations and a meeting room 4m x 5m",
    ],
    "mechanical": [
        "create a gear",
        "40-tooth spur gear, module 3mm, bore 25mm with 8mm keyway",
        "ball bearing 6205 (bore 25mm, OD 52mm, width 15mm)",
        "M8 bolt with hex head",
    ],
    "curved_designs": [
        "smooth butterfly shape",
        "airfoil for aircraft wing",
        "organic blob shape",
        "flowing wave pattern",
    ],
    "complex_designs": [
        "Saturn V rocket silhouette",
        "Disney Cinderella Castle silhouette",
        "princess ball gown silhouette",
    ],
    "edge_cases": [
        "a" * 5000,  # Very long input
        "房子设计",  # Non-ASCII (Chinese)
        "haus design mit fenster",  # German
        "12345",  # Numbers only
        "!@#$%^&*()",  # Special characters only
        "null",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "'; DROP TABLE users; --",  # SQL injection
    ],
}


# Toggle combinations to test
TOGGLE_COMBINATIONS = [
    {
        "auto_accept_mode": False,
        "include_furniture": False,
        "include_annotations": True,
        "quality_level": "professional",
        "refinement_passes": 3
    },
    {
        "auto_accept_mode": True,
        "include_furniture": False,
        "include_annotations": True,
        "quality_level": "professional",
        "refinement_passes": 3
    },
    {
        "auto_accept_mode": False,
        "include_furniture": True,
        "include_annotations": True,
        "quality_level": "professional",
        "refinement_passes": 3
    },
    {
        "auto_accept_mode": True,
        "include_furniture": True,
        "include_annotations": False,
        "quality_level": "draft",
        "refinement_passes": 1
    },
    {
        "auto_accept_mode": True,
        "include_furniture": True,
        "include_annotations": True,
        "quality_level": "standard",
        "refinement_passes": 5
    },
    {
        "auto_accept_mode": False,
        "include_furniture": False,
        "include_annotations": False,
        "quality_level": "professional",
        "refinement_passes": 10
    },
]


def generate_session_id() -> str:
    """Generate unique session ID."""
    import random
    return f"stress_test_{int(time.time())}_{random.randint(1000, 9999)}"


def check_server_health() -> bool:
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def test_chat_endpoint(query: str, settings: Dict[str, Any], session_id: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    Test the /api/chat endpoint.

    Returns: (success, response_data, error_message)
    """
    try:
        payload = {
            "message": query,
            "session_id": session_id,
            "settings": settings
        }

        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=120  # 2 minute timeout for complex queries
        )

        if response.status_code == 200:
            data = response.json()
            return True, data, ""
        else:
            return False, response.json() if response.text else {}, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, {}, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, {}, str(e)
    except json.JSONDecodeError:
        return False, {}, "Invalid JSON response"
    except Exception as e:
        return False, {}, f"Unexpected error: {str(e)}"


def test_generate_endpoint(session_id: str, csv_metadata: str = None) -> Tuple[bool, Dict[str, Any], str]:
    """
    Test the /api/generate endpoint.

    Returns: (success, response_data, error_message)
    """
    try:
        payload = {
            "session_id": session_id,
        }
        if csv_metadata:
            payload["csv_metadata"] = csv_metadata

        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            return True, response.json(), ""
        else:
            return False, response.json() if response.text else {}, f"HTTP {response.status_code}"

    except Exception as e:
        return False, {}, str(e)


def test_generate_multi_endpoint(session_id: str, formats: List[str], csv_metadata: str = None) -> Tuple[bool, Dict[str, Any], str]:
    """
    Test the /api/generate-multi endpoint.

    Returns: (success, response_data, error_message)
    """
    try:
        payload = {
            "session_id": session_id,
            "formats": formats
        }
        if csv_metadata:
            payload["csv_metadata"] = csv_metadata

        response = requests.post(
            f"{BASE_URL}/api/generate-multi",
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            return True, response.json(), ""
        else:
            return False, response.json() if response.text else {}, f"HTTP {response.status_code}"

    except Exception as e:
        return False, {}, str(e)


def test_settings_endpoints(session_id: str) -> List[Tuple[str, bool, str]]:
    """Test settings-related endpoints."""
    results = []

    # Test GET settings
    try:
        response = requests.get(f"{BASE_URL}/api/settings?session_id={session_id}", timeout=10)
        results.append(("GET /api/settings", response.status_code == 200, ""))
    except Exception as e:
        results.append(("GET /api/settings", False, str(e)))

    # Test POST settings
    try:
        response = requests.post(
            f"{BASE_URL}/api/settings",
            json={"session_id": session_id, "settings": {"auto_accept_mode": True}},
            timeout=10
        )
        results.append(("POST /api/settings", response.status_code == 200, ""))
    except Exception as e:
        results.append(("POST /api/settings", False, str(e)))

    # Test reset settings
    try:
        response = requests.post(
            f"{BASE_URL}/api/settings/reset",
            json={"session_id": session_id},
            timeout=10
        )
        results.append(("POST /api/settings/reset", response.status_code == 200, ""))
    except Exception as e:
        results.append(("POST /api/settings/reset", False, str(e)))

    return results


def test_formats_endpoint() -> Tuple[bool, Dict[str, Any], str]:
    """Test the /api/formats endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/api/formats", timeout=10)
        if response.status_code == 200:
            return True, response.json(), ""
        else:
            return False, {}, f"HTTP {response.status_code}"
    except Exception as e:
        return False, {}, str(e)


def test_viewer_status() -> Tuple[bool, Dict[str, Any], str]:
    """Test the /api/viewer/status endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/api/viewer/status", timeout=10)
        if response.status_code == 200:
            return True, response.json(), ""
        else:
            return False, {}, f"HTTP {response.status_code}"
    except Exception as e:
        return False, {}, str(e)


def test_augment_endpoint(session_id: str, augmentation: str) -> Tuple[bool, Dict[str, Any], str]:
    """Test the /api/augment endpoint."""
    try:
        payload = {
            "session_id": session_id,
            "augmentation_request": augmentation
        }
        response = requests.post(
            f"{BASE_URL}/api/augment",
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            return True, response.json(), ""
        else:
            return False, response.json() if response.text else {}, f"HTTP {response.status_code}"
    except Exception as e:
        return False, {}, str(e)


def run_full_stress_test():
    """Run comprehensive stress test."""
    print("=" * 80)
    print("DXF Generator Chatbot - Comprehensive Stress Test")
    print("=" * 80)

    # Check server health
    print("\n[1] Checking server health...")
    if not check_server_health():
        print("ERROR: Server is not running! Start with: python -m backend.server")
        return
    print("Server is healthy.")

    # Test basic endpoints
    print("\n[2] Testing basic endpoints...")

    # Formats endpoint
    success, data, error = test_formats_endpoint()
    print(f"  /api/formats: {'PASS' if success else f'FAIL - {error}'}")

    # Viewer status
    success, data, error = test_viewer_status()
    print(f"  /api/viewer/status: {'PASS' if success else f'FAIL - {error}'}")

    # Settings endpoints
    session_id = generate_session_id()
    settings_results = test_settings_endpoints(session_id)
    for endpoint, success, error in settings_results:
        print(f"  {endpoint}: {'PASS' if success else f'FAIL - {error}'}")

    # Main stress test
    print("\n[3] Running query stress tests...")

    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "errors": [],
        "category_results": {}
    }

    for category, queries in TEST_QUERIES.items():
        print(f"\n  Category: {category}")
        category_results = {"passed": 0, "failed": 0, "tests": []}

        for query in queries:
            # Test with subset of toggle combinations to save time
            toggles_to_test = TOGGLE_COMBINATIONS[:3]  # First 3 combinations

            for settings in toggles_to_test:
                results["total_tests"] += 1
                session_id = generate_session_id()

                query_preview = query[:50] + "..." if len(query) > 50 else query
                query_preview = query_preview.replace("\n", " ")
                settings_preview = f"auto={settings['auto_accept_mode']}, furn={settings['include_furniture']}"

                print(f"    Testing: '{query_preview}' [{settings_preview}]", end=" ")

                start_time = time.time()
                success, data, error = test_chat_endpoint(query, settings, session_id)
                elapsed = time.time() - start_time

                test_result = {
                    "query": query[:100],
                    "settings": settings,
                    "success": success,
                    "error": error,
                    "elapsed_time": elapsed,
                    "has_metadata": bool(data.get("csv_metadata")),
                    "can_generate": data.get("can_generate", False)
                }

                if success:
                    results["passed"] += 1
                    category_results["passed"] += 1
                    print(f"PASS ({elapsed:.2f}s)")

                    # If we can generate, test generation too
                    if data.get("can_generate") and data.get("csv_metadata"):
                        gen_success, gen_data, gen_error = test_generate_endpoint(
                            session_id, data["csv_metadata"]
                        )
                        test_result["generation_success"] = gen_success
                        test_result["generation_error"] = gen_error
                        if not gen_success:
                            print(f"      Generation: FAIL - {gen_error}")
                else:
                    results["failed"] += 1
                    category_results["failed"] += 1
                    print(f"FAIL - {error}")
                    results["errors"].append({
                        "category": category,
                        "query": query[:100],
                        "settings": settings,
                        "error": error
                    })

                category_results["tests"].append(test_result)

        results["category_results"][category] = category_results

    # Test augmentation
    print("\n[4] Testing augmentation endpoint...")

    # First create a design
    session_id = generate_session_id()
    success, data, _ = test_chat_endpoint(
        "simple house with living room 5m x 4m and bedroom 3m x 3m",
        {"auto_accept_mode": True, "include_furniture": False, "include_annotations": True,
         "quality_level": "professional", "refinement_passes": 3},
        session_id
    )

    if success and data.get("csv_metadata"):
        augmentations = [
            "add a window to the living room",
            "make the bedroom larger",
            "add furniture to all rooms",
            "",  # Empty augmentation
            "remove the door",
        ]

        for aug in augmentations:
            aug_preview = aug[:40] if aug else "(empty)"
            print(f"    Augment: '{aug_preview}'", end=" ")
            aug_success, aug_data, aug_error = test_augment_endpoint(session_id, aug)
            if aug_success:
                print("PASS")
            else:
                print(f"FAIL - {aug_error}")
    else:
        print("  Could not create initial design for augmentation tests")

    # Test multi-format generation
    print("\n[5] Testing multi-format generation...")
    session_id = generate_session_id()
    success, data, _ = test_chat_endpoint(
        "simple rectangle 100mm x 50mm",
        {"auto_accept_mode": True, "include_furniture": False, "include_annotations": True,
         "quality_level": "professional", "refinement_passes": 1},
        session_id
    )

    if success and data.get("csv_metadata"):
        format_combos = [
            ["DXF"],
            ["DXF", "STEP"],
            ["DXF", "STL", "OBJ"],
            ["DXF", "STEP", "IGES", "STL", "OBJ", "GLTF"],
            [],  # Empty formats
            ["INVALID_FORMAT"],  # Invalid format
        ]

        for formats in format_combos:
            print(f"    Formats {formats}: ", end="")
            gen_success, gen_data, gen_error = test_generate_multi_endpoint(
                session_id, formats, data["csv_metadata"]
            )
            if gen_success:
                print("PASS")
            else:
                print(f"FAIL - {gen_error}")

    # Print summary
    print("\n" + "=" * 80)
    print("STRESS TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['passed']/results['total_tests']*100:.1f}%")

    print("\nResults by category:")
    for category, cat_results in results["category_results"].items():
        total = cat_results["passed"] + cat_results["failed"]
        rate = cat_results["passed"] / total * 100 if total > 0 else 0
        print(f"  {category}: {cat_results['passed']}/{total} ({rate:.1f}%)")

    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for err in results["errors"][:10]:  # Show first 10 errors
            print(f"  - {err['category']}: {err['query'][:40]}... - {err['error']}")

    # Save detailed results
    results_file = f"stress_test_results_{int(time.time())}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {results_file}")

    return results


if __name__ == "__main__":
    try:
        run_full_stress_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        traceback.print_exc()
